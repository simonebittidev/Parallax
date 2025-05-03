# WebAppTemplate - Documentazione

Questo progetto è un template che combina un'applicazione **Next.js** per il frontend e un'applicazione **Flask** per il backend. Il frontend viene buildato in modo statico e servito tramite Flask.

## Struttura del progetto

- **`/client`**: Contiene il codice del frontend sviluppato con Next.js.
- **`/app.py`**: Configura Flask per servire i file statici generati dal build del frontend.

---

## Requisiti

Assicurati di avere installati i seguenti strumenti:

- **Node.js** (versione consigliata: LTS)
- **Python** (versione 3.7 o superiore)
- **pip** (gestore di pacchetti Python)

---

## Istruzioni per l'installazione e il build

### 1. Installazione dei pacchetti npm

1. Spostati nella directory del frontend:
    ```bash
    cd client
    ```

2. Installa le dipendenze necessarie:
    ```bash
    npm install
    ```

---

### 2. Build statico del frontend

1. Esegui il comando di build per generare i file statici:
    ```bash
    npm run build
    ```

2. Esporta il progetto in formato statico:
    ```bash
    npm run export
    ```

    Questo comando creerà una cartella chiamata **`out`** all'interno della directory **`/client`**. Questa cartella conterrà i file statici del frontend.

---

### 3. Configurazione di Flask

1. Assicurati che **`app.py`** sia configurato per servire i file statici dalla cartella **`/client/out`**. Il file dovrebbe includere una configurazione simile a questa:

    ```python
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

    # Altrimenti, restituisci index.html per gestire le rotte client-side
    return send_from_directory(static_dir, 'index.html')
    ```

2. Installa le dipendenze Python necessarie:
    ```bash
    pip install -r requirements.txt
    ```

3. Avvia il server Flask:
    ```bash
    python app.py
    ```

    Ora il server Flask servirà i file statici generati dal frontend.

---

## Note aggiuntive

- Durante lo sviluppo del frontend, puoi utilizzare il comando **`npm run dev`** per avviare il server di sviluppo di Next.js.
- Ricorda di eseguire nuovamente il comando **`npm run build`** e **`npm run export`** ogni volta che apporti modifiche al frontend e vuoi aggiornare i file statici serviti da Flask.

Buon lavoro!