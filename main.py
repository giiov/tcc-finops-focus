import os
import tempfile
from typing import Literal

import pandas as pd
from fastapi import Depends, FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from src.autenticacao import UsuarioAtual, usuario_atual

from src.assistente.ai.assistente import ErroAssistente, responder
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

@app.get("/eu")
def eu(usuario: UsuarioAtual = Depends(usuario_atual)):
    #devolve o id de quem está logado; serve para o front (e para testes) confirmarem o token
    return {"id": usuario.id}


#def comum (e não async def): o pandas é bloqueante, e assim o fastapi roda a função em outra thread
#sem travar as outras requisições
@app.post("/converter")
def converter(arquivo: UploadFile = File(...)):
    if not (arquivo.filename or "").lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Envie um arquivo com extensão .csv")

    conteudo = arquivo.file.read()
    
    #lê no máximo 1 byte a mais que o limite: se esse byte extra existir, o arquivo passou do limite
    #assim um arquivo gigante nunca é carregado inteiro na memória (o render grátis tem 512 MB)
    limite_bytes = LIMITE_MB * 1024 * 1024
    conteudo = arquivo.file.read(limite_bytes + 1)

    if len(conteudo) > limite_bytes:
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


#o pydantic confere o formato do json que chega, antes de a nossa função rodar
#role só aceita "user" e "assistant": assim ninguém consegue mandar uma mensagem "system" para trocar as instruções da Ada
class Mensagem(BaseModel):
    role: Literal["user", "assistant"]
    #o limite é folgado porque as respostas da Ada também voltam aqui como histórico
    content: str = Field(min_length=1, max_length=10000)


class PedidoAssistente(BaseModel):
    mensagens: list[Mensagem] = Field(min_length=1, max_length=50)


#def comum pelo mesmo motivo do /converter: a chamada ao Groq é bloqueante
@app.post("/assistente")
def assistente(pedido: PedidoAssistente):
    #a conversa precisa terminar numa pergunta do usuário, é a ela que a Ada vai responder
    if pedido.mensagens[-1].role != "user":
        raise HTTPException(status_code=400, detail="A última mensagem precisa ser do usuário.")

    try:
        texto = responder([m.model_dump() for m in pedido.mensagens])
    except ErroAssistente as erro:
        #as mensagens do ErroAssistente já foram escritas para o usuário ler (chave recusada, limite, sem internet...)
        raise HTTPException(status_code=503, detail=str(erro))

    return {"resposta": texto}