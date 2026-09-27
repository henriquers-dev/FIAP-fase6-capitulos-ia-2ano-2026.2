import os import re import shutil from dataclasses import dataclass from typing import Optional, Tuple, List
import joblib from sklearn.feature_extraction.text import TfidfVectorizer from sklearn.linear_model import LogisticRegression
from regras.regras import MotorInferencial, Documento, Decisao
import pytesseract from PIL import Image
try: from pdf2image import convert_from_path except Exception: convert_from_path = None
PASTA_ENTRADA = "entrada" PASTA_PROCESSADO = "processado" PASTA_RELATORIOS = "relatorios" PASTA_MODELOS = "modelos"
DESTINOS = { "suporte": os.path.join(PASTA_PROCESSADO, "suporte"), "comercial": os.path.join(PASTA_PROCESSADO, "comercial"), "financeiro": os.path.join(PASTA_PROCESSADO, "financeiro"), "auditoria": os.path.join(PASTA_PROCESSADO, "auditoria"), "manual": os.path.join(PASTA_PROCESSADO, "manual"), }
MODELO_PATH = os.path.join(PASTA_MODELOS, "modelo.joblib") VEC_PATH = os.path.join(PASTA_MODELOS, "vectorizer.joblib")
@dataclass class ResultadoML: categoria: str confianca: float probs: List[Tuple[str, float]]
@dataclass class Extracao: valor_total: Optional[float] data: Optional[str] cnpj: Optional[str]
def normalizar_texto(txt: str) -> str: txt = txt.lower() txt = re.sub(r"\s+", " ", txt).strip() return txt
def extrair_campos(texto: str) -> Extracao: texto = texto.replace("\n", " ")
m_valor = re.search(
    r"r\$ *(\d{1,3}(?:\.\d{3})*(?:,\d{2})|\d+(?:,\d{2}))",
    texto,
    flags=re.IGNORECASE
)
valor = None
if m_valor:
    bruto = m_valor.group(1).replace(".", "").replace(",", ".")
    try:
        valor = float(bruto)
    except ValueError:
        valor = None

m_data = re.search(r"\b(\d{2}/\d{2}/\d{4})\b", texto)
data = m_data.group(1) if m_data else None

m_cnpj = re.search(r"\b(\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2})\b", texto)
cnpj = m_cnpj.group(1) if m_cnpj else None

return Extracao(valor_total=valor, data=data, cnpj=cnpj)

def ler_texto_de_arquivo(caminho: str) -> str: ext = os.path.splitext(caminho)[1].lower()
if ext == ".txt":
    with open(caminho, "r", encoding="utf-8") as f:
        return f.read()

if ext in [".png", ".jpg", ".jpeg"]:
    img = Image.open(caminho)
    return pytesseract.image_to_string(img, lang="por")

if ext == ".pdf":
    if convert_from_path is None:
        raise RuntimeError("pdf2image não disponível. Instale pdf2image e poppler.")
    paginas = convert_from_path(caminho)
    partes = []
    for pg in paginas:
        partes.append(pytesseract.image_to_string(pg, lang="por"))
    return "\n".join(partes)

raise ValueError(f"Tipo de arquivo não suportado: {ext}")

def treinar_se_nao_existir(): os.makedirs(PASTA_MODELOS, exist_ok=True)
if os.path.exists(MODELO_PATH) and os.path.exists(VEC_PATH):
    return

dados = [
    "erro ao acessar o sistema de autenticação",
    "falha no login do usuário e token inválido",
    "sistema não responde e apresenta timeout",
    "problema ao instalar o aplicativo e erro de dependência",
    "instabilidade no servidor e falha de conexão",

    "pedido de orçamento para 50 licenças",
    "interesse em comprar plano empresarial",
    "solicitação de preços e condições comerciais",
    "cotação de serviço e proposta comercial",
    "informações sobre upgrade e contratação",

    "segunda via de boleto e cobrança em aberto",
    "confirmação de pagamento e comprovante anexado",
    "erro na cobrança e divergência no valor",
    "fatura mensal e vencimento em 10/02/2026",
    "reembolso e estorno do pagamento"
]

labels = [
    "suporte", "suporte", "suporte", "suporte", "suporte",
    "comercial", "comercial", "comercial", "comercial", "comercial",
    "financeiro", "financeiro", "financeiro", "financeiro", "financeiro"
]

vec = TfidfVectorizer(ngram_range=(1, 2), min_df=1)
X = vec.fit_transform([normalizar_texto(t) for t in dados])

clf = LogisticRegression(max_iter=200)
clf.fit(X, labels)

joblib.dump(clf, MODELO_PATH)
joblib.dump(vec, VEC_PATH)

def classificar_texto(texto: str) -> ResultadoML: clf = joblib.load(MODELO_PATH) vec = joblib.load(VEC_PATH)
X = vec.transform([normalizar_texto(texto)])
probs = clf.predict_proba(X)[0]
classes = clf.classes_

pares = sorted([(c, float(p)) for c, p in zip(classes, probs)],
               key=lambda x: x[1],
               reverse=True)
return ResultadoML(categoria=pares[0][0], confianca=pares[0][1], probs=pares)

def inferir_decisao(categoria: str, confianca: float, extracao: Extracao): motor = MotorInferencial() motor.reset()
motor.declare(Documento(
    categoria=categoria,
    confianca=confianca,
    valor_total=extracao.valor_total,
    data=extracao.data,
    cnpj=extracao.cnpj
))

motor.run()

decisoes = []
for f in motor.facts.values():
    if isinstance(f, Decisao):
        decisoes.append(f)
return decisoes

def selecionar_destino(decisoes) -> str: if not decisoes: return DESTINOS["manual"]
prioridade_rank = {"ALTA": 3, "MEDIA": 2, "BAIXA": 1}
ordenadas = sorted(decisoes,
                   key=lambda d: prioridade_rank.get(d["prioridade"], 0),
                   reverse=True)
acao = ordenadas[0]["acao"]

if acao == "AUDITAR":
    return DESTINOS["auditoria"]
if acao == "PROCESSAR":
    return DESTINOS["financeiro"]
if acao == "ENCAMINHAR_SUPORTE":
    return DESTINOS["suporte"]
if acao == "ENCAMINHAR_COMERCIAL":
    return DESTINOS["comercial"]
return DESTINOS["manual"]

def gerar_relatorio(nome_arquivo: str, texto: str, ml: ResultadoML, extr: Extracao, decisoes, destino: str): os.makedirs(PASTA_RELATORIOS, exist_ok=True) rel_path = os.path.join(PASTA_RELATORIOS, f"{nome_arquivo}.relatorio.txt")
with open(rel_path, "w", encoding="utf-8") as f:
    f.write("RELATÓRIO DE PROCESSAMENTO AUTOMATIZADO\n")
    f.write(f"Arquivo: {nome_arquivo}\n")
    f.write(f"Destino operacional: {destino}\n\n")

    f.write("SAÍDA DO MODELO (ML)\n")
    f.write(f"Categoria escolhida: {ml.categoria}\n")
    f.write(f"Confiança estimada: {ml.confianca:.3f}\n")
    f.write("Distribuição de probabilidades:\n")
    for c, p in ml.probs:
        f.write(f"  {c}: {p:.3f}\n")
    f.write("\n")

    f.write("EVIDÊNCIAS EXTRAÍDAS (OCR/Regex)\n")
    f.write(f"Valor total: {extr.valor_total}\n")
    f.write(f"Data: {extr.data}\n")
    f.write(f"CNPJ: {extr.cnpj}\n\n")

    f.write("DECISÕES INFERIDAS (MOTOR DE REGRAS)\n")
    if not decisoes:
        f.write("Nenhuma decisão inferida. Encaminhado para revisão manual.\n")
    else:
        for d in decisoes:
            f.write(f"- acao={d['acao']} prioridade={d['prioridade']} motivo={d['motivo']}\n")
    f.write("\n")

    f.write("TRECHO DO TEXTO PROCESSADO (AMOSTRA)\n")
    f.write(normalizar_texto(texto)[:600] + "\n")

def processar_arquivo(caminho: str): nome = os.path.basename(caminho) base = os.path.splitext(nome)[0]
texto = ler_texto_de_arquivo(caminho)
extr = extrair_campos(texto)

ml = classificar_texto(texto)
decisoes = inferir_decisao(ml.categoria, ml.confianca, extr)

destino = selecionar_destino(decisoes)
os.makedirs(destino, exist_ok=True)

gerar_relatorio(base, texto, ml, extr, decisoes, destino)
shutil.move(caminho, os.path.join(destino, nome))

print(f"\nPROCESSADO: {nome}")
print(f"Categoria: {ml.categoria}  Confiança: {ml.confianca:.3f}")
print(f"Valor: {extr.valor_total}  Data: {extr.data}  CNPJ: {extr.cnpj}")
print(f"Destino: {destino}")

def preparar_pastas(): os.makedirs(PASTA_ENTRADA, exist_ok=True) os.makedirs(PASTA_PROCESSADO, exist_ok=True) for p in DESTINOS.values(): os.makedirs(p, exist_ok=True) os.makedirs(PASTA_RELATORIOS, exist_ok=True) os.makedirs(PASTA_MODELOS, exist_ok=True)
def main(): preparar_pastas() treinar_se_nao_existir()
arquivos = [os.path.join(PASTA_ENTRADA, a) for a in os.listdir(PASTA_ENTRADA)]
arquivos = [a for a in arquivos if os.path.isfile(a)]

if not arquivos:
    print("Nenhum arquivo em 'entrada/'. Adicione .txt, .png, .jpg, .jpeg ou .pdf e execute novamente.")
    return

for caminho in arquivos:
    try:
        processar_arquivo(caminho)
    except Exception as e:
        print(f"\nERRO ao processar {os.path.basename(caminho)}: {e}")
        os.makedirs(DESTINOS["manual"], exist_ok=True)
        shutil.move(caminho, os.path.join(DESTINOS["manual"], os.path.basename(caminho)))

if name == "main": main()
