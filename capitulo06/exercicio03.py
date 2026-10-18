import asyncio
from agents import Agent, Runner, handoff
from google.colab import userdata
import os

analista_vendas = Agent(
    name="AnalistaVendas",
    instructions="Analise dados de vendas e identifique padrões de demanda.",
    model='gpt-4o-mini'
)

estrategista = Agent(
    name="Estrategista",
    instructions="Sugira ações estratégicas com base em análises de negócio.",
    model='gpt-4o-mini'
)


triage_agent = Agent(
    name="TriageAgent",
    instructions="""
    Você é um agente de triagem.

    Se a tarefa envolver:
    - análise de vendas → envie para o AnalistaVendas
    - tomada de decisão estratégica → envie para o Estrategista
    """,
    handoffs=[
        analista_vendas,
        handoff(estrategista)
    ],
    model='gpt-4o-mini'
)


async def run_agent():
  resultado = await Runner.run(
    triage_agent,
    "Baseado na análise: Demanda baixa detectada, o que fazer?")
  print(resultado.final_output)

await run_agent()
