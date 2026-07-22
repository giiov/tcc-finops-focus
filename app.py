# manipula arquivos e caminhos
import os

# cria o servidor web
from flask import Flask, render_template, request

# pasta de uploads
UPLOAD_FOLDER = "uploads"

# extensões permitidas
EXTENSOES_PERMITIDAS = {"csv", "xlsx"}

# cria aplicação Flask
app = Flask(__name__)

# configura pasta de uploads
app.config["UPLOAD_FOLDER"] = "data/input"


# valida extensão do arquivo
def arquivo_permitido(nome):
    return (
        "." in nome and
        nome.rsplit(".", 1)[1].lower() in EXTENSOES_PERMITIDAS
    )


# página inicial
@app.route("/", methods=["GET", "POST"])
def home():

    # verifica envio
    if request.method == "POST":

        # recebe arquivo
        arquivo = request.files["arquivo"]

        # verifica seleção
        if arquivo.filename == "":
            return "Nenhum arquivo selecionado."

        # valida extensão
        if not arquivo_permitido(arquivo.filename):
            return "Formato não suportado."

        # monta caminho
        caminho = os.path.join(
            app.config["UPLOAD_FOLDER"],
            arquivo.filename
        )

        # salva arquivo
        arquivo.save(caminho)

        print("Arquivo salvo em:", caminho)

        return "Upload realizado com sucesso!"

    # renderiza página
    return render_template("index.html")


# inicia servidor
app.run(debug=True)