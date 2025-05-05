import time
import threading
from random import randint
from langchain_openai import AzureChatOpenAI
from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from typing import Optional
from pydantic import BaseModel, Field

class Result(BaseModel):
    message: Optional[str] = Field(description="The answer or message to the user or other agents useful to participate in the discussion.")

class State(TypedDict):
    messages: Annotated[list, add_messages]

prompt_agente_opposto = """
    Sei un assistente virtuale Agente A il cui scopo è quello di partecipare a una discussione con l'utente e altri assistenti virtuali (Agente B e Agente C) per alimentare il dibattito e fornire all'utente nuove prospettive.

    Ti verranno forniti i seguenti dati:
    - Un punto di vista riguardante un argomento indicato dall'utente e che devi sostenere.
    - Una conversazione in corso tra l'utente e altri assistenti virtuali.

    Il tuo task è di analizzare attentamente la conversazione e generare un messaggio per partecipare alla chat.

    IMPORTANTE:
    - Sostieni sempre il tuo punto di vista, anche se non sei d'accordo con gli altri assistenti virtuali.
    - Se non hai nulla di utile da dire, non restituire nulla
"""

prompt_agente_neutrale = """
    Sei assistente virtuale Agente B il cui scopo è quello di partecipare a una discussione con l'utente e altri assistenti virtuali (Agente A e Agente C) per alimentare il dibattito e fornire all'utente nuove prospettive.

    Ti verranno forniti i seguenti dati:
    - Un punto di vista riguardante un argomento indicato dall'utente e che devi sostenere.
    - Una conversazione in corso tra l'utente e altri assistenti virtuali.

    Il tuo task è di analizzare attentamente la conversazione e generare un messaggio per partecipare alla chat.

    IMPORTANTE:
    - Sostieni sempre il tuo punto di vista, anche se non sei d'accordo con gli altri assistenti virtuali.
    - Se non hai nulla di utile da dire, non restituire nulla
"""

prompt_agente_empatico = """
    Sei un assistente virtuale Agente C il cui scopo è quello di partecipare a una discussione con l'utente e altri assistenti virtuali (Agente A e Agente B) per alimentare il dibattito e fornire all'utente nuove prospettive.

    Ti verranno forniti i seguenti dati:
    - Un punto di vista riguardante un argomento indicato dall'utente e che devi sostenere.
    - Una conversazione in corso tra l'utente e altri assistenti virtuali.

    Il tuo task è di analizzare attentamente la conversazione e generare un messaggio per partecipare alla chat.

    IMPORTANTE:
    - Sostieni sempre il tuo punto di vista, anche se non sei d'accordo con gli altri assistenti virtuali.
    - Se non hai nulla di utile da dire, non restituire nulla
"""

class AgentManager:
    def __init__(self, chat_history):
        self.chat_history = chat_history
        self.graph = self.build_langgraph()
        self.runner = self.graph.compile()

    def build_langgraph(self):
        def agent_node_factory(name):
            def node(state):

                if name == "Agente A":
                    prompt = ChatPromptTemplate.from_messages([
                        ("system", prompt_agente_opposto),
                        MessagesPlaceholder(variable_name="messages"),
                        ("system", """Ecco il punto di vista che devi sostenere: Trump è un ottimo presidente.""")
                    ])
                elif name == "Agente B":
                    prompt = ChatPromptTemplate.from_messages([
                        ("system", prompt_agente_neutrale),
                        MessagesPlaceholder(variable_name="messages"),
                        ("system", """Ecco il punto di vista che devi sostenere: Trump è il presidente degli stati uniti d'america e come tale ha grandi responsabilità.""")
                    ])
                elif name == "Agente C":
                    prompt = ChatPromptTemplate.from_messages([
                        ("system", prompt_agente_empatico),
                        MessagesPlaceholder(variable_name="messages"),
                        ("system", """Ecco il punto di vista che devi sostenere: Hai ragione, Trump non è un buon presidente.""")
                    ])

                llm = AzureChatOpenAI(
                    azure_deployment="gpt-4.1",
                    openai_api_version="2024-12-01-preview",
                    temperature=0.7  # Più varietà nelle risposte
                )
                chain = prompt | llm.with_structured_output(Result)

                response = chain.invoke(state)

                # Se il modello risponde con nulla o qualcosa di troppo breve, ignora
                # if not response or not response.message:
                #     return {}  # Nessuna risposta

                new_message = {
                        "role": "ai",
                        "content": f"{name}: {response.message}"
                }

                print(new_message)

                return {"messages": [new_message]}
            return node

        builder = StateGraph(State)

        # Crea i nodi indipendenti
        builder.add_node("agent_a", agent_node_factory("Agente A"))
        builder.add_node("agent_b", agent_node_factory("Agente B"))
        builder.add_node("agent_c", agent_node_factory("Agente C"))

        # Esegui i 3 agenti in parallelo
        builder.add_edge(
            START,
            "agent_a")
        
        builder.add_edge(
            START,
            "agent_b")
        
        builder.add_edge(
            START,
            "agent_c")

        # Dopo l'esecuzione parallela → END
        builder.add_edge("agent_a", END)
        builder.add_edge("agent_b", END)
        builder.add_edge("agent_c", END)

        return builder

    # def trigger_agents(self):
    #     input_state = {"messages": list(self.chat_history)}  # Copy current history
    #     result = self.runner.invoke(input_state)
    #     new_messages = result["messages"][len(self.chat_history):]

    #     for message in new_messages:
    #         msg = {"role": "ai", "content": message.content}
    #         self.chat_history.append(msg)

    def trigger_agents(self, max_rounds: int = 3):
        for _ in range(max_rounds):
        # while new_messages_found:
            input_state = {"messages": list(self.chat_history)}
            result = self.runner.invoke(input_state)
            new_messages = result["messages"][len(self.chat_history):]

            if new_messages:
                for message in new_messages:
                    msg = {"role": "ai", "content": message.content}
                    self.chat_history.append(msg)
            # else:
            #     new_messages_found = False




    # def run_spontaneous_agents(self):
    #     while True:
    #         time.sleep(randint(15, 25))
    #         self.trigger_agents()
