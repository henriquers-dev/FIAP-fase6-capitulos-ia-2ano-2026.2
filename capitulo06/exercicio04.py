from agents import Agent, Runner, WebSearchTool
import asyncio

agent = Agent(
    name="AgentePesquisa",
    instructions="Pesquise a internet usando WebSearchTool quando necessário para dar respostas mais atuais.",
    tools=[WebSearchTool()],
    model='gpt-4o-mini'
)

async def main():
  res = await Runner.run(agent, "Quem venceu a Copa do Mundo de clubes em 2025 e quantos gols o artilheiro fez nessa edição?")
  print("Resposta:", res.final_output)

await main()
