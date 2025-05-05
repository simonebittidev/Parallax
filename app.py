from dotenv import load_dotenv
from flask import Flask, request, jsonify, send_from_directory
from llm_utils.agentv2 import AgentManager
import threading
import os
from flask import Flask, request, jsonify
from llm_utils.llm_pov import create_pov

load_dotenv()

app = Flask(
    __name__,
    static_folder='client/out',
    template_folder='client/out'
)

chat_history = []

agent_manager = AgentManager(chat_history)

@app.route("/messages", methods=["POST"])
def post_message():
    data = request.get_json()
    message = {"role": "user", "content": data["text"]}
    chat_history.append(message)
    agent_manager.trigger_agents()
    return jsonify(success=True), 200

@app.route("/messages", methods=["GET"])
def get_messages():
    return jsonify(chat_history)

@app.route("/api/processpov", methods=["POST"])
def process_point_of_yout():
    data = request.get_json()
    perspective = data.get('perspective')
    user_text = data.get('userText')

    print("Perspective:", perspective)
    print("User Text:", user_text)
    
    rewritten_text = create_pov(perspective, user_text)

    return jsonify({'pov': rewritten_text})

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    static_dir = app.static_folder
    full_path = os.path.join(static_dir, path)

    # Se il percorso è una directory, cerca un index.html al suo interno
    if os.path.isdir(full_path):
        index_file = os.path.join(full_path, 'index.html')
        if os.path.exists(index_file):
            return send_from_directory(full_path, 'index.html')

    # Se il file esiste così com'è, servilo
    if os.path.exists(full_path):
        return send_from_directory(static_dir, path)

    # Se il file con estensione .html esiste, servilo
    html_path = f"{full_path}.html"
    if os.path.exists(html_path):
        return send_from_directory(static_dir, f"{path}.html")

    return send_from_directory(static_dir, 'index.html')

if __name__ == '__main__':
    # threading.Thread(target=agent_manager.run_spontaneous_agents, daemon=True).start()
    app.run(host='0.0.0.0', port=5005, debug=True)