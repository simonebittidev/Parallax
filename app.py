from flask import Flask, render_template, request, jsonify
from langchain_openai import AzureChatOpenAI
from langchain.schema import HumanMessage, SystemMessage
import os
from dotenv import load_dotenv
import json

app = Flask(__name__)

load_dotenv()

pov_prompt = """ 
Ti verranno fornite le seguenti informazioni:
- Un testo che rappresenta un'opinione, un pensiero o una frase scritta dall'utente.
- Un punto di vista selezionato dall'utente, che può essere: Opposto, Neutrale, oppure Empatico.

Il tuo compito è analizzare il testo fornito e generare una nuova opinione o pensiero coerente con il punto di vista indicato.

Linee guida per ciascun punto di vista:
- Opposto: riscrivi l'opinione dell'utente assumendo una posizione contraria.
- Neutrale: formula una frase che non esprima né accordo né disaccordo, mantenendo una prospettiva oggettiva o distaccata.
- Empatico: riscrivi la frase esprimendo accordo e comprensione verso il punto di vista dell’utente.

Nota:
Se il testo dell’utente non è sufficientemente chiaro o non contiene un'opinione interpretabile, restituisci una stringa vuota.

La tua risposta deve consistere solo nella frase riscritta, senza spiegazioni o testo aggiuntivo.
"""

def create_pov_from_text(text, mode):
    llm = AzureChatOpenAI(
        azure_deployment="gpt-4.1",
        openai_api_version="2024-12-01-preview",
        temperature=0,
        max_retries=2
    )

    messages = [
        SystemMessage(content=pov_prompt),
        HumanMessage(content=f"Testo: {text}\nPunto di vista: {mode}"),
    ]

    response = llm.invoke(messages).content
    return response

@app.route("/")
def index():
    return render_template("landing.html")

@app.route('/api/rewriter', methods=['POST'])
def rewriter():
    data = request.get_json()
    user_text = data.get('text', '')
    selected_perspective = data.get('selectedPerspective', '')

    res  = create_pov_from_text(user_text, selected_perspective)
    
    print(res)
    return jsonify({"pov": res})

@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.get_json()
    message = data.get('message', '')
    perspective = data.get('perspective', 'neutrale')

    # Simula una risposta nella chat
    response = {
        "reply": f"({perspective.capitalize()}) Hai detto: '{message}'. Ecco cosa penso..."
    }
    return jsonify(json.loads(response))

@app.route("/tryout")
def tryout():
    return render_template("tryout.html")

if __name__ == "__main__":
    app.run(debug=True)