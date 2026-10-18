from dotenv import load_dotenv
from anthropic import Anthropic
import pandas as pd


dados = pd.DataFrame({
    "mes": ["Jan", "Fev", "Mar"],
    "vendas": [120, 95, 140]
})


def agente_dados(df):
    return df.describe().to_string()


def agente_explicador(client, analise):
    prompt = f"Explique os seguintes indicadores de vendas para um gestor:\n\n{analise}"
    resposta = client.messages.create(
        model="claude-sonnet-5-5",
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )
    return "".join(
        bloco.text for bloco in resposta.content if bloco.type == "text"
    )


def main():
    load_dotenv()
    client = Anthropic()

    analise = agente_dados(dados)
    explicacao = agente_explicador(client, analise)
    print(explicacao)


if __name__ == "__main__":
    main()
