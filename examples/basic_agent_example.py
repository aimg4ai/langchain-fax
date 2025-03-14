"""
Example of using the Fax.Plus LangChain integration in an agent
"""

import os
from langchain.agents import initialize_agent, AgentType
from langchain.llms import OpenAI
from langchain.memory import ConversationBufferMemory

# Import our custom tool
from langchain_fax import FaxPlusTool, FaxPlusStatusTool

def main():
    # Set up the tools
    fax_tool = FaxPlusTool(
        api_key=os.environ.get("FAXPLUS_API_KEY"),
        account_id=os.environ.get("FAXPLUS_ACCOUNT_ID")
    )

    fax_status_tool = FaxPlusStatusTool(
        api_key=os.environ.get("FAXPLUS_API_KEY"),
        account_id=os.environ.get("FAXPLUS_ACCOUNT_ID")
    )

    # Set up the LLM
    llm = OpenAI(temperature=0)

    # Create a memory
    memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)

    # Initialize the agent with the tools
    agent = initialize_agent(
        tools=[fax_tool, fax_status_tool],
        llm=llm,
        agent=AgentType.CHAT_CONVERSATIONAL_REACT_DESCRIPTION,
        memory=memory,
        verbose=True
    )

    # Example conversation
    response = agent.run(
        "Please send a fax of my report.pdf file to +14155552671 with the subject 'Monthly Report'"
    )
    print(response)

if __name__ == "__main__":
    main()