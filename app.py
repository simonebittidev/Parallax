from flask import Flask, render_template, request, jsonify
from langchain_openai import AzureChatOpenAI
from langchain.schema import HumanMessage, SystemMessage
import os
from dotenv import load_dotenv

app = Flask(__name__)

load_dotenv()

llm = AzureChatOpenAI(
        azure_deployment="gpt-4.1",
        openai_api_version="2024-12-01-preview",
        temperature=0,
        max_retries=2
    )

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/reformulate", methods=["POST"])
def reformulate():
    data = request.get_json()
    text = data.get("text", "")
    perspective = data.get("perspective", "neutrale")

    mock_responses = {
        "opposto": f"Non sono d'accordo con te. In realtà, potremmo vedere la questione in modo totalmente diverso: '{text[::-1]}'",
        "neutrale": f"Analizzando il tuo pensiero in modo oggettivo: '{text}'. Ci sono pro e contro da considerare.",
        "empatico": f"Capisco molto bene cosa intendi. Il tuo pensiero '{text}' riflette una sensibilità importante."
    }

    response = mock_responses.get(perspective, text)
    return jsonify({"reformulated": response})

@app.route("/api/chat", methods=["POST"])
def chat():
    data = request.get_json()
    user_message = data.get("message", "")
    perspective = data.get("perspective", "neutrale")

    reply = f"[{perspective.capitalize()} bot]: Ho letto il tuo messaggio: '{user_message}'. Ecco cosa penso a riguardo..."

    return jsonify({"reply": reply})

if __name__ == "__main__":
    app.run(debug=True)