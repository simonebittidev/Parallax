from flask import Flask, send_from_directory
import os

app = Flask(
    __name__,
    static_folder='client/out',
    template_folder='client/out'
)

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
    app.run(host='0.0.0.0', port=5000, debug=True)