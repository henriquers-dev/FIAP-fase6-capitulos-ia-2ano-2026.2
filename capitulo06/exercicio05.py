from agents import Agent, Runner, function_tool
import requests
import asyncio

@function_tool
def consulta_clima(cidade: str) -> dict:
    # Suponha que exista uma API REST local que retorna JSON como:
    # {"temperature": 25.3, "condition": "ensolarado"}
    # Para este exemplo, vamos simular uma resposta.
    if cidade.lower() == "fortaleza":
        return {"temperature": 30.5, "condition": "ensolarado"}
    else:
        return {"temperature": 20.0, "condition": "desconhecido"}

agent = Agent(
    name="AgenteClimaAvancado",
    instructions="Use a ferramenta `consulta_clima(cidade)` para responder sobre clima de forma precisa.",
    tools=[consulta_clima],
    model='gpt-4o-mini'
)

async def main():
    result = await Runner.run(agent, "Como está o tempo em Fortaleza hoje?")
    print("Resposta:", result.final_output)

await main()
