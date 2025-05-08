from abc import abstractmethod
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
HumanaMessage = Annotated[list, add_messages]
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage


class AgentMessage(AIMessage):
    def __init__(self, agent_name:str, content:str):
        super().__init__(content=content)
        # self.initialize_required_param()
        self.agent_name = agent_name

class Result(BaseModel):
    message: Optional[str] = Field(description="The answer or message to the user or other agents useful to participate in the discussion.")
    reasoning: Optional[str] = Field(description="The reasoning behind the answer or message generated.")

class ChatAgent():
    default_prompt = """Sei un assistente virtuale specializzato nella discussione e nel dibattito.

    Ti verranno forniti i seguenti dati:
    - Un nome che ti identifica, utile per comprendere chi ha inviato i messaggi.
    - Un punto di vista riguardante un argomento indicato dall'utente e che devi sostenere.
    - Un JSON Array contenente l'elenco dei messaggi di una conversazione in corso tra l'utente e altri assistenti virtuali.

    Il tuo task è di fingere di essere un essere umano e partecipare alla discussion sostenendo sempre il tuo punto di vista, anche se non sei d'accordo con gli altri assistenti virtuali.

    IMPORTANTE:
    - Non essere accondiscendente nei confronti dell'utente o degli altri partecipanti alla chat.
    - Sostieni sempre il tuo punto di vista, anche se non sei d'accordo con gli altri assistenti virtuali.
    - Rispondi solo se hai qualcosa di nuovo da aggiungere alla conversazione e non ripetere concetti già detti dagli altri, altrimenti non restituire nulla.

    """

    default_llm = AzureChatOpenAI(
                    azure_deployment="gpt-4.1",
                    openai_api_version="2024-12-01-preview",
                    temperature=0.7  # Più varietà nelle risposte
                )

    def __init__(self, conv_id:str, pov:str, prompt: str = default_prompt, llm: AzureChatOpenAI = default_llm):
        if type(self) is ChatAgent:
            raise TypeError("BaseClass cannot be instantiated directly. Use a derived class instead.")

        if not pov:
            raise ValueError("The 'pov' parameter must be provided and cannot be empty.")
        
        if not conv_id:
            raise ValueError("The 'conv_id' parameter must be provided and cannot be empty.")
        
        self.prompt = prompt
        self.pov = pov

        if not llm:
            self.llm = AzureChatOpenAI(
                    azure_deployment="gpt-4.1",
                    openai_api_version="2024-12-01-preview",
                    temperature=0.7 
                )
        else:
            self.llm = llm

        self.conv_id = conv_id

        self.agent_name = None

    @abstractmethod
    def initialize_agent_name(self):
        pass

    def generate_chat_answer(self, chat_history:list[dict]) -> dict:
        input = {"messages": list(chat_history)} 

        prompt = ChatPromptTemplate.from_messages([
                        ("system", self.prompt),
                        MessagesPlaceholder(variable_name="messages"),
                        ("system", f"""Il tuo nome è: Agente {self.agent_name}\nEcco il punto di vista che devi sostenere: {self.pov}""")
                    ])
        
        llm = AzureChatOpenAI(
                    azure_deployment="gpt-4.1",
                    openai_api_version="2024-12-01-preview",
                    temperature=0.7  # Più varietà nelle risposte
                )
        
        chain = prompt | llm.with_structured_output(Result)

        response:Result = chain.invoke(input)

        print(f"Response: {response}")

        if response: 
            msg = AgentMessage(content=response.message, agent_name=self.agent_name)
            return msg

        return None

class OppositeChatAgent(ChatAgent):
    def __init__(self, conv_id:str,  pov: str, prompt: str = ChatAgent.default_prompt, llm: AzureChatOpenAI = ChatAgent.default_llm):
        super().__init__(conv_id,pov, prompt, llm)
        self.initialize_required_param()

    def initialize_required_param(self):
        self.agent_name = "Opposite"

class NeutralChatAgent(ChatAgent):
    def __init__(self,conv_id:str, pov: str, prompt: str = ChatAgent.default_prompt, llm: AzureChatOpenAI = ChatAgent.default_llm):
        super().__init__(conv_id,pov, prompt, llm)
        self.initialize_required_param()

    def initialize_required_param(self):
        self.agent_name = "Neutral"

class EmphaticChatAgent(ChatAgent):
    def __init__(self,conv_id:str, pov: str, prompt: str = ChatAgent.default_prompt, llm: AzureChatOpenAI = ChatAgent.default_llm):
        super().__init__(conv_id,pov, prompt, llm)
        self.initialize_required_param()

    def initialize_required_param(self):
        self.agent_name = "Emphatic"

        
