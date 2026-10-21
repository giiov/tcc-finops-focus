
# a única responsabilidade desse arquivo é conectar ao groq

import os
from dotenv import load_dotenv
from groq import Groq

#lê o arquivo ".env" (se ele existir) e coloca o que está dentro dele
# nas variáveis de ambiente de computador
load_dotenv()

#modelo usado se não for definidop no GROQ_MODEL no .env
MODELO_PADRAO = "openai/gpt-oss-120b"

class chave_nao_configurada(Exception):
    #usado quando não achamos a chave de API
    pass

def buscar_chave():
    #busca chave de api em dois lugares na ordem abaixo
    chave = os.getenv("GROQ_API_KEY")

    if chave:
        return chave

    try:
        import streamlit as st

        return st.secrets.get("GROQ_API_KEY")
    except Exception:
        return None

def obter_modelo():
    #devolve o nome do modelo
    return os.getenv("GROQ_MODEL", MODELO_PADRAO)

def criar_cliente():
    #cria o objeto que conversa com o Groq
    chave = buscar_chave()

    if not chave:
        raise chave_nao_configurada(
            "Chave da Api do Groq não encontrada."
            "Crie um arquivo .env com GROQ_API_KEY=sua chave"
        )

    #timeout=30 -> se o groq não responder em 30s, desistimos
    #max_retries=1 -> se der um erro passageiro, tenta mais de uma vez sozinho
    return Groq(api_key=chave,
                timeout=30,
                max_retries=1)
