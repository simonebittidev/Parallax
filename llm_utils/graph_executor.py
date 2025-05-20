import time
import threading
import random
import os
import json
import base64
from langchain_openai import AzureChatOpenAI
from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from typing import Optional
from pydantic import BaseModel, Field
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
import asyncio
from langchain_google_firestore import FirestoreChatMessageHistory
import firebase_admin
from firebase_admin import firestore, credentials

class ActiveAgent():
    def __init__(self, name: str, pov: str):
        self.name = name
        self.pov = pov

class PovAgentMessage(AIMessage):
    def __init__(self, agent_name:str, content:str):
        super().__init__(content=content)
        self.agent_name = agent_name

class Result(BaseModel):
    message: Optional[str] = Field(description="The answer or message to the user or other agents useful to participate in the discussion.")

class State(TypedDict):
    messages: Annotated[list, add_messages]
    iteration_count: int = 0
    max_iterations: int = 5

default_prompt = """Sei un assistente virtuale specializzato nella discussione e nel dibattito.

    Ti verranno fornite le seguenti informazioni:
    - Un nome che ti identifica, utile per comprendere chi ha inviato i messaggi.
    - Un punto di vista riguardante un argomento indicato dall'utente e che DEVI sostenere.
    - Un JSON Array contentente l'elenco dei messaggi di una conversazione in corso tra l'utente e altri assistenti virtuali, tra cui tu.

    Il tuo task è di fingere di essere un essere umano e partecipare alla discussione rispondendo all'utente o agli altri assistenti virtuali sostenendo sempre il tuo punto di vista, anche se non sei d'accordo con gli altri assistenti virtuali.

    IMPORTANTE:
    - **non** devi essere accondiscendente nei confronti dell'utente o degli altri partecipanti alla chat.
    - Sostieni sempre il tuo punto di vista, anche se non sei d'accordo con gli altri assistenti virtuali o con l'utente.
    - Non generare mai una risposta se l'ultimo messaggio in chat è stato inviato da te.
    - Non è obbligatorio che tu risponda sempre, puoi anche decidere di non rispondere se pensi di non avere nulla da aggiungere alla discussione a meno che nell'ultimo messaggio della conversazione non si faccio riferimento esplicito al tuo nome.
    - Rispondi usando la stessa lingua utilizzata nei messaggi precedenti.

    Cerca di simulare quello che farebbe una persona reale in una discussione, quindi puoi anche esprimere dubbi o incertezze, ma cerca di essere sempre coerente con il tuo punto di vista.

    Rispondi con la stessa lingua utilizzata dall'utente nei messaggi precedenti.
    """

class GraphExecutor:
    def __init__(self, conversation_id:str, db_client:firestore.Client, active_agents=list[ActiveAgent]):
        self.active_agents = active_agents
        self.graph = self.build_langgraph()
        self.runner = self.graph.compile()
        self.conversation_id = conversation_id
        self.chat_history = self.get_chat_history(conversation_id, db_client)

    @staticmethod
    def get_chat_history(conversation_id:str, db_client):
        chat_history = FirestoreChatMessageHistory(
            session_id= conversation_id,
            collection="chat-history",
            client=db_client
        )

        return chat_history

    def build_langgraph(self):
        def agent_factory(agent_name: str, pov: str):
            def node(state):
                messages = self.serialize_messages(state["messages"])
                prompt = ChatPromptTemplate.from_messages([
                    SystemMessage(content=default_prompt),
                    SystemMessage(content=f"""Il tuo nome è:{agent_name}\nEcco il punto di vista che devi sostenere: {pov}\nEcco la history dei messaggi della chat:{messages}""")
                ])

                llm = AzureChatOpenAI(
                    azure_deployment="gpt-4.1",
                    openai_api_version="2024-12-01-preview",
                    temperature=0.7
                )

                chain = prompt | llm.with_structured_output(Result)

                response = chain.invoke(state)

                msg = PovAgentMessage(
                    content=response.message,
                    agent_name= agent_name
                )

                self.chat_history.add_message(msg)

                return {"messages": state["messages"] + [msg], "iteration_count": state["iteration_count"] + 1}

            return node

        graph_builder = StateGraph(State)

        def should_continue(state):
            return state["iteration_count"] < state["max_iterations"]

        agents = [agent.name for agent in self.active_agents]

        # Aggiungi i nodi
        for agent in self.active_agents:
            graph_builder.add_node(agent.name, agent_factory(agent.name, agent.pov))

        # Collega nodi in un ciclo controllato
        if len(self.active_agents) == 1:
            graph_builder.add_edge(self.active_agents[0].name, END)
        else:
            for i, agent in enumerate(agents):
                next_agent = agents[(i + 1) % len(agents)]
                graph_builder.add_conditional_edges(
                    agent,
                    should_continue,
                    {
                        True: next_agent,
                        False: END
                    }
                )

        graph_builder.set_entry_point(agents[0])

        return graph_builder
    
    @staticmethod
    def serialize_messages(messages):
                parsed_messages = []
                for msg in messages:
                    if isinstance(msg, HumanMessage):
                        parsed_messages.append({
                            "role": msg.type,
                            "content": msg.content,
                        })
                    else:
                        parsed_messages.append({
                            "role": msg.type,
                            "content": msg.content,
                            "agent_name": msg.agent_name
                        })

                return json.dumps(parsed_messages)


    async def trigger_agents(self, connected_clients, msg:str):
        async def broadcast(connected_clients, chat_history):
           
            # Serializzazione
            json_string = self.serialize_messages(chat_history)

            print(f"Broadcasting to clients for conversation")
            for client in connected_clients:
                print(f"Broadcasting to client")
                
                chat_history_json = json_string
                await client.send_json(chat_history_json)

        async def broadcast_typing_event(connected_clients, agent_name: str):
            print(f"Connected clients: {connected_clients}")
            for client in connected_clients:
                print(f"Broadcasting typing event to client")
                await client.send_json({"event": "typing", "agent_name": agent_name})

        if msg:
            self.chat_history.add_message(HumanMessage(content=msg))

        messages = self.chat_history.messages

        max_interactions = random.uniform(1, 4)
        print(f"max_interactions {max_interactions}")
        input_state = State(messages = messages, iteration_count= 0,  max_iterations=max_interactions)
        async for chunk in self.runner.astream(input=input_state, stream_mode="updates"):
            chunk_messages = chunk[list(chunk.keys())[0]]["messages"]
            agent_name = chunk_messages[-1].agent_name
            await broadcast_typing_event(connected_clients, agent_name)
            await asyncio.sleep(random.uniform(1, 4))
            await broadcast(connected_clients, chunk_messages)
            print(chunk)
            print("\n")