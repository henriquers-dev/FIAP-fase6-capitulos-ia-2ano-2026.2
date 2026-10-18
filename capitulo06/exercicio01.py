from openai import OpenAI
from google.colab import userdata
from os import environ

environ['OPENAI_API_KEY'] = userdata.get('OPENAI_API_KEY')

client = OpenAI()

def agente_leitor(texto):
    prompt = f"Leia o seguinte relatório e extraia os pontos principais:\n\n{texto}"
    resposta = client.responses.create(
        model="gpt-4o-mini",
        input=prompt
    )
    return resposta.output_text

def agente_analista(resumo):
    prompt = f"Com base nos pontos principais abaixo, gere recomendações estratégicas:\n\n{resumo}"
    resposta = client.responses.create(
        model="gpt-4o-mini",
        input=prompt
    )
    return resposta.output_text

relatorio = "As vendas caíram 12% no último trimestre devido à ruptura de estoque e baixa visibilidade promocional."

pontos = agente_leitor(relatorio)
recomendacoes = agente_analista(pontos)

print(recomendacoes)
