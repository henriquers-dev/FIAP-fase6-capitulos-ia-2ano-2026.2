import os
import re
import pandas as pd
import pytesseract
from pdf2image import convert_from_path
import spacy
import unicodedata
from difflib import SequenceMatcher

# ==============================================
# CONFIGURAÇÕES INICIAIS
# ==============================================
# Observação: instale o modelo antes com:
#   python -m spacy download pt_core_news_sm
# E garanta o Tesseract com o idioma 'por' instalado.
nlp = spacy.load("pt_core_news_sm")


def normalizar_texto(txt):
    if not txt:
        return ""
    txt = txt.lower()
    txt = unicodedata.normalize("NFKD", txt)
    txt = "".join([c for c in txt if not unicodedata.combining(c)])
    txt = re.sub(r'[^a-z0-9\s/]', ' ', txt)
    txt = re.sub(r'\s+', ' ', txt)
    return txt.strip()


def similar(a, b):
    return SequenceMatcher(None, normalizar_texto(a), normalizar_texto(b)).ratio()


# ==============================================
# FUNÇÃO OCR
# ==============================================
def extrair_texto_pdf(caminho_pdf):
    """
    Converte um arquivo PDF em imagens e aplica OCR para extrair o texto.
    """
    paginas = convert_from_path(caminho_pdf, dpi=300)
    texto = ""
    for pagina in paginas:
        # Se 'por' não estiver instalado, troque para 'eng' temporariamente
        texto += pytesseract.image_to_string(pagina, lang='por') + "\n"
    return texto


# ==============================================
# FUNÇÃO DE BUSCA FLEXÍVEL POR LABELS
# ==============================================
def buscar_por_label(texto, lista_labels, janela=60):
    texto_norm = normalizar_texto(texto)
    for label in lista_labels:
        label_norm = normalizar_texto(label)
        # Busca aproximada tolerante a OCR
        for match in re.finditer(label_norm[:6], texto_norm):
            inicio = match.start()
            trecho = texto_norm[inicio: inicio + len(label_norm) + janela]
            if similar(trecho, label_norm) > 0.7:
                padrao_valor = re.search(label_norm + r'[:/ -]*([a-z0-9\s.-&]+)', trecho)
                if padrao_valor:
                    return padrao_valor.group(1).strip()
    return None


# ==============================================
# EXTRAÇÃO DO CABEÇALHO
# ==============================================
def extrair_entidades(texto):
    """
    Extrai campos principais de uma NF com tolerância fonética e estrutural.
    """
    texto_limpo = normalizar_texto(texto)

    # Padrões fixos
    padrao_cnpj = re.search(r'\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}', texto)
    padrao_chave = re.search(r'(\d[\d\s]{40,})', texto)
    padrao_valor = re.search(r'r?\$ ?\d{1,3}(?:\.\d{3})*,\d{2}', texto, re.IGNORECASE)
    padrao_data = re.search(r'\b(?:[0-3]?\d[/.-][01]?\d[/.-](?:\d{4}|\d{2}))\b', texto)
    padrao_numero = re.search(r'(?:n[ºo]|numero|nf)[\s:]*([0-9]{3,})', texto_limpo)
    padrao_serie = re.search(r'serie[:\s]*([0-9a-z]+)', texto_limpo)

    # Sinonímias e variações estruturais
    labels = {
        "razao_social": ["razao social", "nome / razao social", "emitente", "empresa", "nome razao social", "nome do emitente"],
        "natureza_operacao": ["natureza da operacao", "finalidade da operacao", "tipo de operacao", "natureza op", "natureza da operação"],
        "inscricao_estadual": ["inscricao estadual", "i e", "ie", "inscr estadual"]
    }

    razao = buscar_por_label(texto, labels["razao_social"])
    natureza = buscar_por_label(texto, labels["natureza_operacao"])
    inscricao = buscar_por_label(texto, labels["inscricao_estadual"])

    # Fallback semântico com spaCy
    if not razao:
        doc = nlp(texto)
        for ent in doc.ents:
            if ent.label_ in ["ORG"]:
                razao = ent.text.strip()
                break

    return {
        "CNPJ Emitente": padrao_cnpj.group(0) if padrao_cnpj else None,
        "Razão Social": razao,
        "Número NF": padrao_numero.group(1) if padrao_numero else None,
        "Série": padrao_serie.group(1) if padrao_serie else None,
        "Data de Emissão": padrao_data.group(0) if padrao_data else None,
        "Valor Total": padrao_valor.group(0) if padrao_valor else None,
        "Natureza da Operação": natureza,
        "Chave de Acesso": re.sub(r'\s+', '', padrao_chave.group(1)) if padrao_chave else None,
        "Inscrição Estadual": inscricao
    }


# ==============================================
# EXTRAÇÃO DOS ITENS
# ==============================================
def extrair_itens(texto):
    """
    Extrai itens do detalhamento da NF-e.
    Retorna uma lista de dicionários: Código, Descrição, Quantidade, Unidade, Valor Unitário.
    Funciona mesmo sem títulos explícitos por meio de heurísticas.
    """
    texto_limpo = re.sub(r'[^\w\s,.-/]', ' ', texto)
    linhas = [l.strip() for l in texto_limpo.split("\n") if l.strip()]

    # 1) Procurar início/fim de forma flexível
    inicio_idx, fim_idx = None, None
    for i, linha in enumerate(linhas):
        ln = normalizar_texto(linha)
        if any(p in ln for p in [
            "itens da nota", "itens nota", "detalhamento dos produtos",
            "dados dos produtos", "produto servico", "cod do produto",
            "codigo descricao qtde", "descricao dos produtos"
        ]):
            inicio_idx = i + 1
        if any(p in ln for p in [
            "total da nota", "resumo dos valores", "valores totais", "total geral"
        ]):
            fim_idx = i
            break

    # 2) Fallback por padrão de linhas com números/valores
    if inicio_idx is None:
        for i, linha in enumerate(linhas):
            if re.search(r'^\d{1,5}\s+[A-Z].+\d{1,3}(?:[.,]\d{3})*,\d{2}', linha):
                inicio_idx = max(i - 1, 0)
                break

    if fim_idx is None:
        fim_idx = len(linhas)

    if inicio_idx is None:
        # Detecção por densidade numérica
        blocos = []
        bloco = []
        for l in linhas:
            if re.search(r'\d', l):
                bloco.append(l)
            elif bloco:
                blocos.append(bloco)
                bloco = []
        if bloco:
            blocos.append(bloco)

        if blocos:
            blocos_validos = [b for b in blocos if len([l for l in b if re.search(r'\d{1,3},\d{2}', l)]) >= 3]
            if blocos_validos:
                bloco_itens = max(blocos_validos, key=len)
            else:
                return []
        else:
            return []
    else:
        bloco_itens = linhas[inicio_idx:fim_idx]

    # 3) Agrupar linhas quebradas pelo OCR
    itens = []
    item_atual = ""
    for linha in bloco_itens:
        if re.match(r'^\d{1,6}\s', linha):  # nova linha de item indica início por código
            if item_atual:
                itens.append(item_atual.strip())
            item_atual = linha
        else:
            item_atual += " " + linha
    if item_atual:
        itens.append(item_atual.strip())

    # 4) Extrair campos
    registros = []
    for item in itens:
        codigo = re.search(r'^\d{1,6}', item)
        qtd = re.search(r'(\d+(?:[.,]\d+)?)\s*(UN|KG|LT|CX|PC|PÇ|UNID)', item, re.IGNORECASE)
        valores = re.findall(r'(\d{1,3}(?:\.\d{3})*,\d{2})', item)
        descricao = re.sub(r'^\d{1,6}\s+', '', item)
        descricao = re.sub(r'\s{2,}', ' ', descricao)

        registros.append({
            "Código": codigo.group(0) if codigo else None,
            "Descrição": descricao.strip() if descricao else None,
            "Quantidade": qtd.group(1) if qtd else None,
            "Unidade": (qtd.group(2).upper() if qtd else None),
            "Valor Unitário": (valores[-1] if valores else None)
        })

    return registros


# ==============================================
# SALVAR CSV DE ITENS
# ==============================================
def salvar_itens_csv(itens, arquivo_saida="itens_nota.csv"):
    if not itens:
        print("Nenhum item encontrado para salvar.")
        return
    df = pd.DataFrame(itens)
    df.to_csv(arquivo_saida, index=False, sep=";")
    print(f"Itens salvos em {arquivo_saida} ({len(df)} linhas).")


# ==============================================
# PIPELINE PRINCIPAL
# ==============================================
def processar_pasta(diretorio):
    resultados = []
    for arquivo in os.listdir(diretorio):
        if arquivo.lower().endswith(".pdf"):
            caminho = os.path.join(diretorio, arquivo)
            print(f"\nProcessando {arquivo}...")
            try:
                texto = extrair_texto_pdf(caminho)
                dados = extrair_entidades(texto)
                dados["Arquivo"] = arquivo
                resultados.append(dados)

                itens = extrair_itens(texto)
                if itens:
                    salvar_itens_csv(itens, arquivo_saida=f"itens_{os.path.splitext(arquivo)[0]}.csv")

            except Exception as e:
                print(f"Erro ao processar {arquivo}: {e}")
    return pd.DataFrame(resultados)


# ==============================================
# EXECUÇÃO PRINCIPAL
# ==============================================
if __name__ == "__main__":
    pasta = "notas_fiscais"
    saida = "dados_extraidos.csv"

    if not os.path.exists(pasta):
        print(f"Pasta '{pasta}' não encontrada. Crie uma pasta chamada '{pasta}' e coloque PDFs dentro dela.")
    else:
        df = processar_pasta(pasta)
        if not df.empty:
            df.to_csv(saida, index=False, sep=";")
            print(f"\nCabeçalhos extraídos e salvos em {saida}")
        else:
            print("\nNenhum dado foi extraído. Verifique os PDFs e o OCR.")
