import os
import sys

import anthropic
from dotenv import load_dotenv

MODELO = "claude-sonnet-5-5"

SYSTEM_LEITOR = (
    "Você é um analista de dados especializado em leitura de relatórios. "
    "Extraia apenas os pontos principais, de forma objetiva, em tópicos curtos. "
    "Não invente informações que não estejam no texto."
)

SYSTEM_ANALISTA = (
    "Você é um consultor de estratégia de negócios. "
    "A partir dos pontos recebidos, gere recomendações práticas e priorizadas, "
    "cada uma com uma breve justificativa."
)


def verificar_chave():
    """Diagnostica a variável ANTHROPIC_API_KEY sem expor seu conteúdo."""
    chave = os.environ.get("ANTHROPIC_API_KEY")
    print("=== DIAGNÓSTICO DA CHAVE ===")

    if not chave:
        sys.exit(
            "ANTHROPIC_API_KEY não está definida neste terminal.\n"
            'Defina com: export ANTHROPIC_API_KEY="sk-ant-api..." '
            '(Mac/Linux) ou $env:ANTHROPIC_API_KEY="sk-ant-api..." (PowerShell).'
        )

    print(f"Chave carregada (tamanho: {len(chave)} caracteres).")

    if chave != chave.strip().strip('"').strip("'"):
        print("PROBLEMA: a chave tem espaços ou aspas extras. Redefina sem eles.")
    if chave.startswith("sk-ant-admin"):
        print("PROBLEMA: esta é uma chave Admin e não funciona para mensagens.")
    elif not chave.startswith("sk-ant-api"):
        print("PROBLEMA: o formato não parece uma chave de API (sk-ant-api...).")
    print()


def chamar_modelo(client, prompt, system, max_tokens=1024):
    """Chama a API e devolve o texto da resposta, tratando os erros mais comuns."""
    try:
        resposta = client.messages.create(
            model=MODELO,
            max_tokens=max_tokens,
            system=system,
            messages=[{"role": "user", "content": prompt}],
        )
    except anthropic.AuthenticationError as e:
        sys.exit(f"Erro: chave de API inválida. Detalhe da API: {e.message}")
    except anthropic.NotFoundError:
        sys.exit(f"Erro: modelo '{MODELO}' não encontrado.")
    except anthropic.RateLimitError:
        sys.exit("Erro: limite de requisições atingido. Tente novamente em instantes.")
    except anthropic.APIConnectionError:
        sys.exit("Erro: falha de conexão com a API.")
    except anthropic.APIStatusError as e:
        sys.exit(f"Erro da API ({e.status_code}): {e.message}")

    if resposta.stop_reason == "max_tokens":
        print(
            "Aviso: a resposta foi cortada por atingir max_tokens.",
            file=sys.stderr,
        )

    return "".join(b.text for b in resposta.content if b.type == "text")


def agente_leitor(client, texto):
    prompt = f"Leia o seguinte relatório e extraia os pontos principais:\n\n{texto}"
    return chamar_modelo(client, prompt, SYSTEM_LEITOR)


def agente_analista(client, resumo):
    prompt = f"Com base nos pontos principais abaixo, gere recomendações estratégicas:\n\n{resumo}"
    return chamar_modelo(client, prompt, SYSTEM_ANALISTA)


if __name__ == "__main__":
    load_dotenv()
    verificar_chave()
    client = anthropic.Anthropic()

    relatorio = (
        "As vendas caíram 12% no último trimestre devido à ruptura de estoque "
        "e baixa visibilidade promocional."
    )

    print("=== RELATÓRIO ===")
    print(relatorio, "\n")

    pontos = agente_leitor(client, relatorio)
    print("=== PONTOS PRINCIPAIS (agente leitor) ===")
    print(pontos, "\n")

    recomendacoes = agente_analista(client, pontos)
    print("=== RECOMENDAÇÕES (agente analista) ===")
    print(recomendacoes)
