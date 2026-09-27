"""
    PDF2Image é um módulo que converte arquivos PDF em imagens. Ele utiliza bibliotecas como PyMuPDF ou pdf2image para realizar a conversão, permitindo que cada página do PDF seja transformada em uma imagem separada. O módulo pode ser configurado para definir a resolução das imagens geradas,
    o formato de saída (como PNG ou JPEG) e outras opções de personalização.
"""

import os
import platform
import tempfile
import types
import shutil
import subprocess
import contextlib
from subprocess import Popen, PIPE, TimeoutExpired
from typing import Any, Union, Tuple, List, Dict, Callable
from pathlib import PurePath
from PIL import Image

from pdf2image.generators import (
    uuid_generator,
    counter_generator,
    ThreadSafeGenerator
)

from pdf2image.parsers import (
    parse_buffer_to_pgm,
    parse_buffer_to_ppm,
    parse_buffer_to_jpeg,
    parse_buffer_to_png
)

from pdf2image.exceptions import (
    PDFInfoNotInstalledError,
    PDFPageCountError,
    PDFSyntaxError,
    PDFPopplerTimeoutError
)

TRANSPARENT_FILE_TYPES = ["png", "tiff"]
PDF_INFO_CONVERT_TO_INT = ["Pages"]


def convert_from_path(
        pdf_path: Union[str, PurePath],
        dpi: int = 200,
        output_folder: Union[str, PurePath] = None,
        first_page: int = None,
        last_page: int = None,
        fmt: str = "ppm",
        jpegopt: Dict[str, Any] = None,
        thread_count: int = 1,
        userpw: str = None,
        ownerpw: str = None,
        use_cropbox: bool = False,
        strict: bool = False,
        transparent: bool = False,
        single_file: bool = False,
        output_file: Union[str, Callable[..., str]] = uuid_generator(),
        poppler_path: Union[str, PurePath] = None,
        grayscale: bool = False,
        size: Union[Tuple[int, int], Tuple[int, None], int] = None,
        paths_only: bool = False,
        use_pdftocairo: bool = False,
        timeout: int = None,
        hide_annotations: bool = False,
) -> Union[List[Image.Image], List[str]]:
    """
    Description: Convert PDF to Image will throw whenever one of the condition is reached
    Parameters:
        pdf_path -> Path to the PDF that you want to convert
        dpi -> Image quality in DPI (default 200)
        output_folder -> Write the resulting images to a folder (instead of directly in memory)
        first_page -> First page to process
        last_page -> Last page to process before stopping
        fmt -> Output image format
        jpegopt -> jpeg options `quality`, `progressive`, and `optimize` (only for jpeg format)
        thread_count -> How many threads we are using for conversion (default 1)
        userpw -> PDF's password
        ownerpw -> PDF's owner password
        use_cropbox -> Use cropbox instead of mediabox
        strict -> When a Syntax Error is thrown, it will be raised as an Exception
        transparent -> Output with a transparent background instead of a white one
        single_file -> Uses the -singlefile option from pdftoppm/pdftocairo
        output_file -> What is used to build the output file name
        poppler_path -> Path to look for poppler binaries
        grayscale -> Output grayscale image(s)
        size -> Size of the resulting image(s), uses the Pillow (width, height) standard
        paths_only -> Don't load image(s), return paths instead (requires output_folder)
        use_pdftocairo -> Use pdftocairo instead of pdftoppm, may help with image quality in some cases
        timeout -> Raise a PDFPopplerTimeoutError when timeout (in seconds) is reached
        hide_annotations -> Hide PDF annotations in the output images
    """

    if use_pdftocairo and fmt == "ppm":
        fmt = "png"

    if not paths_only and output_folder is not None and not os.path.exists(output_folder):
        raise ValueError("output_folder must be a valid existing directory when set")

    if paths_only and output_folder is None:
        raise NotImplementedError(
            "output_folder must be set when paths_only=True"
        )

    page_count = pdfinfo_from_path(
        pdf_path, userpw, ownerpw, poppler_path=poppler_path
    )["Pages"]

    if first_page is None or first_page < 1:
        first_page = 1

    if last_page is None or last_page > page_count:
        last_page = page_count

    if first_page > last_page:
        return []

    # Recalculate page count based on first and last page
    page_count = last_page - first_page + 1

    if thread_count < 1:
        thread_count = 1

    if thread_count > page_count:
        thread_count = page_count

    # pdftocairo can only stream a single page to stdout (with -singlefile);
    # for anything else it must write to real files. So whenever pdftocairo
    # is going to be used (explicitly, or implicitly because a transparent
    # background was requested) and the caller didn't give us an
    # output_folder, fall back to a throwaway temp directory and read the
    # results back into memory before cleaning it up.
    effective_use_pdftocairo = use_pdftocairo or (
        transparent and fmt in TRANSPARENT_FILE_TYPES
    )
    use_temp_folder = output_folder is None and effective_use_pdftocairo

    with tempfile.TemporaryDirectory() if use_temp_folder else _null_context() as temp_dir:
        working_folder = temp_dir if use_temp_folder else output_folder

        reminder = page_count % thread_count
        current_page = first_page
        processes = []
        for _ in range(thread_count):
            # Get the number of pages this thread will be handling
            thread_page_count = page_count // thread_count + (
                1 if reminder > 0 else 0
            )
            # Build the command accordingly
            args, parse_buffer_func, resolved_output_file = _build_command(
                ["-r", str(dpi), pdf_path],
                working_folder,
                current_page,
                current_page + thread_page_count - 1,
                fmt,
                jpegopt,
                userpw,
                ownerpw,
                use_cropbox,
                transparent,
                single_file,
                output_file,
                use_pdftocairo,
                grayscale,
                size,
                hide_annotations,
            )
            current_page = current_page + thread_page_count
            reminder -= 1 if reminder > 0 else 0
            # Spawn the process and save its resolved output-file prefix (used
            # later to collect the pages this thread produced, when writing
            # to a folder)
            processes.append(
                (resolved_output_file, _spawn_process(args, poppler_path))
            )

        images = []

        for uid, proc in processes:
            data, err = proc.communicate(timeout=timeout)

            if b"Syntax Error" in err and strict:
                raise PDFSyntaxError(err.decode("utf8", "ignore"))

            if working_folder is not None:
                images += _load_from_output_folder(
                    working_folder,
                    uid,
                    in_memory=paths_only is False or use_temp_folder,
                )
            else:
                images += parse_buffer_func(data)

        if use_temp_folder:
            # Force PIL to read the file content now, since the backing
            # temp directory is about to be deleted.
            images = [img.copy() for img in images]

        return images


def convert_from_bytes(
        pdf_file: bytes,
        dpi: int = 200,
        output_folder: Union[str, PurePath] = None,
        first_page: int = None,
        last_page: int = None,
        fmt: str = "ppm",
        jpegopt: Dict[str, Any] = None,
        thread_count: int = 1,
        userpw: str = None,
        ownerpw: str = None,
        use_cropbox: bool = False,
        strict: bool = False,
        transparent: bool = False,
        single_file: bool = False,
        output_file: Union[str, Callable[..., str]] = uuid_generator(),
        poppler_path: Union[str, PurePath] = None,
        grayscale: bool = False,
        size: Union[Tuple[int, int], Tuple[int, None], int] = None,
        paths_only: bool = False,
        use_pdftocairo: bool = False,
        timeout: int = None,
        hide_annotations: bool = False,
) -> Union[List[Image.Image], List[str]]:
    """
    Description: Convert PDF (from in-memory bytes) to Image, delegates to convert_from_path
    by writing the bytes to a temporary file first.
    """
    with tempfile.NamedTemporaryFile(suffix=".pdf") as f:
        f.write(pdf_file)
        f.flush()
        return convert_from_path(
            f.name,
            dpi=dpi,
            output_folder=output_folder,
            first_page=first_page,
            last_page=last_page,
            fmt=fmt,
            jpegopt=jpegopt,
            thread_count=thread_count,
            userpw=userpw,
            ownerpw=ownerpw,
            use_cropbox=use_cropbox,
            strict=strict,
            transparent=transparent,
            single_file=single_file,
            output_file=output_file,
            poppler_path=poppler_path,
            grayscale=grayscale,
            size=size,
            paths_only=paths_only,
            use_pdftocairo=use_pdftocairo,
            timeout=timeout,
            hide_annotations=hide_annotations,
        )


def pdfinfo_from_path(
        pdf_path: Union[str, PurePath],
        userpw: str = None,
        ownerpw: str = None,
        poppler_path: Union[str, PurePath] = None,
        rawdates: bool = False,
        timeout: int = None,
        first_page: int = None,
        last_page: int = None,
) -> Dict[str, Any]:
    """
    Description: Function to get information about a PDF using pdfinfo (from poppler)
    """
    args = _resolve_poppler_binary("pdfinfo", poppler_path)

    if rawdates:
        args.append("-rawdates")

    if first_page is not None:
        args.extend(["-f", str(first_page)])

    if last_page is not None:
        args.extend(["-l", str(last_page)])

    if userpw is not None:
        args.extend(["-upw", userpw])

    if ownerpw is not None:
        args.extend(["-opw", ownerpw])

    args.append(pdf_path)

    try:
        proc = Popen(args, env=_get_command_env(poppler_path), stdout=PIPE, stderr=PIPE)
    except OSError:
        raise PDFInfoNotInstalledError(
            "Unable to get page count. Is poppler installed and in PATH?"
        )

    try:
        out, err = proc.communicate(timeout=timeout)
    except TimeoutExpired:
        proc.kill()
        outs, errs = proc.communicate()
        raise PDFPopplerTimeoutError("Page info timed out.")

    if b"Syntax Error" in err:
        raise PDFSyntaxError(err.decode("utf8", "ignore"))

    d = {}
    for field in out.decode("utf8", "ignore").split("\n"):
        sf = field.split(":")
        key, value = sf[0], ":".join(sf[1:]).strip()
        if key in PDF_INFO_CONVERT_TO_INT:
            value = int(value)
        d[key] = value

    if "Pages" not in d:
        raise PDFPageCountError(
            "Unable to get page count.\n%s" % err.decode("utf8", "ignore")
        )

    return d


@contextlib.contextmanager
def _null_context():
    """A no-op context manager, used when we don't need a temp directory."""
    yield None


def _get_command_env(poppler_path: Union[str, PurePath] = None):
    env = os.environ.copy()
    if poppler_path is not None:
        env["PATH"] = f"{poppler_path}{os.pathsep}{env.get('PATH', '')}"
    return env


def _resolve_poppler_binary(binary_name: str, poppler_path: Union[str, PurePath] = None) -> List[str]:
    if platform.system() == "Windows":
        binary_name = binary_name + ".exe"

    if poppler_path is not None:
        full_path = os.path.join(str(poppler_path), binary_name)
        return [full_path]

    return [binary_name]


def _spawn_process(args: List[str], poppler_path: Union[str, PurePath] = None) -> Popen:
    return Popen(
        args,
        env=_get_command_env(poppler_path),
        stdout=PIPE,
        stderr=PIPE,
    )


def _build_command(
        args: List[str],
        output_folder: Union[str, PurePath],
        first_page: int,
        last_page: int,
        fmt: str,
        jpegopt: Dict[str, Any],
        userpw: str,
        ownerpw: str,
        use_cropbox: bool,
        transparent: bool,
        single_file: bool,
        output_file: Union[str, Callable[..., str]],
        use_pdftocairo: bool,
        grayscale: bool,
        size: Union[Tuple[int, int], Tuple[int, None], int],
        hide_annotations: bool,
) -> Tuple[List[str], Callable[[bytes], List[Any]], Union[str, None]]:
    # -transp (transparent background) is only understood by pdftocairo, so
    # force that binary whenever a transparent output was requested.
    use_pdftocairo = use_pdftocairo or (
        transparent and fmt in TRANSPARENT_FILE_TYPES
    )
    binary_name = "pdftocairo" if use_pdftocairo else "pdftoppm"
    command_args = [binary_name]
    command_args += args

    parse_buffer_func = parse_buffer_to_ppm

    if fmt in ("jpg", "jpeg"):
        command_args.append("-jpeg")
        parse_buffer_func = parse_buffer_to_jpeg
    elif fmt == "png":
        command_args.append("-png")
        parse_buffer_func = parse_buffer_to_png
    elif fmt in ("tif", "tiff"):
        command_args.append("-tiff")
    elif fmt == "pgm":
        parse_buffer_func = parse_buffer_to_pgm

    if jpegopt:
        if "quality" in jpegopt:
            command_args += ["-jpegopt", f"quality={jpegopt['quality']}"]
        if "progressive" in jpegopt:
            command_args += ["-jpegopt", f"progressive={'y' if jpegopt['progressive'] else 'n'}"]
        if "optimize" in jpegopt:
            command_args += ["-jpegopt", f"optimize={'y' if jpegopt['optimize'] else 'n'}"]

    if use_cropbox:
        command_args.append("-cropbox")

    if hide_annotations:
        command_args.append("-hide-annotations")

    if transparent and fmt in TRANSPARENT_FILE_TYPES:
        command_args.append("-transp")

    if grayscale:
        command_args.append("-gray")

    if size is not None:
        if isinstance(size, tuple) and len(size) == 2:
            width, height = size
            if width is not None:
                command_args += ["-scale-to-x", str(width)]
            else:
                command_args += ["-scale-to-x", "-1"]
            if height is not None:
                command_args += ["-scale-to-y", str(height)]
            else:
                command_args += ["-scale-to-y", "-1"]
        elif isinstance(size, int):
            command_args += ["-scale-to", str(size)]

    if first_page is not None:
        command_args += ["-f", str(first_page)]

    if last_page is not None:
        command_args += ["-l", str(last_page)]

    if userpw is not None:
        command_args += ["-upw", userpw]

    if ownerpw is not None:
        command_args += ["-opw", ownerpw]

    if single_file:
        command_args.append("-singlefile")

    resolved_output_file = None
    if output_folder is not None:
        if isinstance(output_file, str):
            resolved_output_file = output_file
        elif hasattr(output_file, "__next__"):
            # e.g. uuid_generator()/counter_generator(), which yield a new
            # name each time next() is called
            resolved_output_file = next(output_file)
        elif callable(output_file):
            resolved_output_file = output_file()
        else:
            resolved_output_file = str(output_file)

        command_args.append(
            os.path.join(str(output_folder), resolved_output_file)
        )

    return command_args, parse_buffer_func, resolved_output_file


def _load_from_output_folder(
        output_folder: Union[str, PurePath],
        output_file_prefix: str,
        in_memory: bool = True,
) -> Union[List[Image.Image], List[str]]:
    matching_files = sorted(
        f for f in os.listdir(output_folder)
        if f.startswith(str(output_file_prefix))
    )

    paths = [os.path.join(str(output_folder), f) for f in matching_files]

    if not in_memory:
        return paths

    return [Image.open(p) for p in paths]
