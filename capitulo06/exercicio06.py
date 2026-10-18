from agents import Agent, handoff

billing_agent = Agent(name="BillingAgent", instructions="Responda dúvidas de cobrança.", model='gpt-4o-mini')
refund_agent = Agent(name="RefundAgent", instructions="Cuide de pedidos de reembolso.", model='gpt-4o-mini')

triage_agent = Agent(
    name="TriageAgent",
    instructions="Direcione questões de cobrança ou reembolso aos agentes apropriados.",
    handoffs=[billing_agent, handoff(refund_agent)],
    model='gpt-4o-mini'

)
