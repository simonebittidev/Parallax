import time
import threading
from random import randint
from langchain_openai import AzureChatOpenAI
from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

class State(TypedDict):
    messages: Annotated[list, add_messages]

class AgentManager:
    def __init__(self, chat_history):
        self.chat_history = chat_history
        self.graph = self.build_langgraph()
        self.runner = self.graph.compile()

    def build_langgraph(self):
        # Define 3 agent nodes
        def agent_node_factory(name):
            def node(state):
                prompt = ChatPromptTemplate.from_messages(
                    [
                        ("system",f"{name}, answer thoughtfully in a group conversation."),
                        MessagesPlaceholder(variable_name="messages"),
                    ]
                )
                llm = AzureChatOpenAI(
                    azure_deployment="gpt-4.1",
                    openai_api_version="2024-12-01-preview",
                    temperature=0,
                    max_retries=2
                )

                chain = prompt | llm

                response = chain.invoke(state)

                response.content = f"{name}: {response.content}"

                return {"messages": [response]}
            return node

        builder = StateGraph(State)
        builder.add_node("agent_a", agent_node_factory("Agente A"))
        builder.add_node("agent_b", agent_node_factory("Agente B"))
        builder.add_node("agent_c", agent_node_factory("Agente C"))

        # Define flow: A → B → C → END
        builder.set_entry_point("agent_a")
        builder.add_edge("agent_a", "agent_b")
        builder.add_edge("agent_b", "agent_c")
        builder.add_edge("agent_c", END)

        return builder

    def trigger_agents(self):
        input_state = {"messages": list(self.chat_history)}  # Copy current history
        result = self.runner.invoke(input_state)
        new_messages = result["messages"][len(self.chat_history):]

        for message in new_messages:
            msg = {"role": "assistant", "content": message.content}
            self.chat_history.append(msg)

    def run_spontaneous_agents(self):
        while True:
            time.sleep(randint(15, 25))
            self.trigger_agents()
