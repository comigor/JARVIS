import langchain
from langchain.chains import LLMMathChain
from langchain.agents import initialize_agent, Tool
from langchain.agents import AgentType
from langchain.chat_models import ChatOpenAI

langchain.debug = True

llm = ChatOpenAI(temperature=0, model="gpt-3.5-turbo-0613", openai_api_base='http://127.0.0.1:8080/v1')
llm_math_chain = LLMMathChain.from_llm(llm=llm, verbose=True)
tools = [
    Tool(
        name="Calculator",
        func=llm_math_chain.run,
        description="useful for when you need to answer questions about math"
    )
]

mrkl = initialize_agent(tools, llm, agent=AgentType.OPENAI_MULTI_FUNCTIONS, verbose=True)

aaa = mrkl.run("What is the square root of the year of birth of the founder of Space X?")
# aaa = mrkl.run("Hello, how are you doing?")

print(aaa)
