import os
import tempfile

import pandas as pd
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from src.conversao import FormatoNaoReconhecido, converter_arquivo, tabela_para_registros

#mesmo limite do frontend (50 MB); o servidor confere de novo porque o frontend pode ser burlado
LIMITE_MB = 50

#quantas linhas da tabela FOCUS voltam na resposta (a tabela inteira pode ter milhares)
LINHAS_AMOSTRA = 100

app = FastAPI(title="FOCUS Multi-Cloud API")

#CORS: o navegador só deixa o site em localhost:5173 (vite) falar com a api em localhost:8000
#se a api não autorizar essa origem. FRONTEND_URLS permite acrescentar o endereço do vercel depois
origens = ["http://localhost:5173", "http://127.0.0.1:5173"]
origens += [u for u in os.getenv("FRONTEND_URLS", "").split(",") if u]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origens,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def status():
    #rota para testar rápido se a api está de pé
    return {"status": "ok"}


#def comum (e não async def): o pandas é bloqueante, e assim o fastapi roda a função em outra thread
#sem travar as outras requisições
@app.post("/converter")
def converter(arquivo: UploadFile = File(...)):
    if not (arquivo.filename or "").lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Envie um arquivo com extensão .csv")

    conteudo = arquivo.file.read()

    if len(conteudo) > LIMITE_MB * 1024 * 1024:
        raise HTTPException(status_code=413, detail=f"O arquivo passa do limite de {LIMITE_MB} MB.")

    #os conversores recebem um caminho de arquivo, então salvamos o upload numa pasta temporária
    #o "with" apaga a pasta (e o csv) sozinho no fim, mesmo se der erro
    with tempfile.TemporaryDirectory() as pasta:
        caminho = os.path.join(pasta, "entrada.csv")
        with open(caminho, "wb") as f:
            f.write(conteudo)

        try:
            formato, df_focus = converter_arquivo(caminho)
        except (pd.errors.EmptyDataError, pd.errors.ParserError, UnicodeDecodeError):
            raise HTTPException(status_code=400, detail="Não consegui ler o arquivo como CSV.")
        except FormatoNaoReconhecido:
            raise HTTPException(status_code=422, detail="Não foi possível identificar o provedor do arquivo.")

    return {
        "formato": formato,
        "total_linhas": len(df_focus),
        "colunas": list(df_focus.columns),
        "amostra": tabela_para_registros(df_focus, LINHAS_AMOSTRA),
    }