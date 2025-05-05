 
from typing import Optional
from langchain_openai import AzureChatOpenAI
from langchain.schema import HumanMessage, SystemMessage
from langchain_openai import AzureChatOpenAI
from pydantic import BaseModel, Field

# Pydantic
class Pov(BaseModel):
    pov: Optional[str] = Field(description="The new point of view generated based on the provided text and the requested alternative point of view.")

def create_pov(perspective:str, text:str):
    """Generate an alternative point of view based on the provided text and perspective.
    This function uses an Azure OpenAI Chat model to analyze the given text and 
    generate a new point of view based on the specified perspective. The output 
    is returned as a JSON object containing the generated point of view.
    Args:
        perspective (str): The type of alternative point of view to generate. 
            It can be one of the following:
            - "Opposite": A completely opposite point of view to the one provided.
            - "Neutral": A point of view that neither expresses approval nor disapproval 
                but simply describes the facts.
            - "Empathetic": A point of view that seeks to understand and share the 
                emotions or experiences of the author of the original text.
        text (str): The input text containing an opinion or point of view on a topic.
    Returns:
        dict: A JSON object with the following key:
            - "pov": The new point of view generated based on the provided text 
                and the requested perspective.
        If the input text is not sufficiently long or lacks relevant information 
        to generate a new point of view, the function returns None."""
    
    llm = AzureChatOpenAI(
        azure_deployment="gpt-4.1",
        openai_api_version="2024-12-01-preview",
        temperature=0,
        max_retries=2
    )
    
    prompt = """
        You are a virtual assistant expert in generating new points of view based on a text provided by the user.
        
        You will be given the following information:
        - A text provided by the user containing an opinion or a point of view on a topic.
        - An alternative point of view that the user wants to explore, which can be one of the following:
            1. Opposite: a completely opposite point of view to the one provided.
            2. Neutral: a point of view that neither expresses approval nor disapproval but simply describes the facts.
            3. Empathetic: a point of view that seeks to understand and share the emotions or experiences of the author of the original text.

        Your task is to carefully analyze the provided text and generate a short text, or even just a sentence, that expresses the requested alternative point of view.

        Follow these instructions:
        - Try to articulate the new point of view in a clear and concise manner.
        - Ensure that the new point of view is relevant to the original text and aligns with the requested perspective.
        - Avoid using any personal opinions or biases in your response.

        Return the output as a JSON with the following keys:
        - "pov": the new point of view generated based on the provided text and the requested alternative point of view.

        Examples:
        Perspective: Opposite
        Text: "Trump is a terrible president."
        Generated Point of View: "Trump is a great president."
        ###
        Perspective: Neutral
        Text: "Trump is a terrible president."
        Generated Point of View: "Trump has been criticized by many for his presidency and his policies."
        ###
        Perspective: Empathetic
        Text: "It is understandable to feel disappointed by Trump: many of his choices and communication styles have left a sense of frustration and distrust in those who hoped for something different."

        Note:
        If the provided text is not sufficiently long or does not contain relevant information to generate a new point of view, then do not return anything.
        """

    messages = [
        SystemMessage(content=prompt),
        HumanMessage(content=f"Perspective: {perspective}\nText: {text}"),
    ]

    response = llm.with_structured_output(Pov).invoke(messages)

    return response.pov