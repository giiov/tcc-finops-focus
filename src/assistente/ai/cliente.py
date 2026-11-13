#a única responsabilidade desse arquivo é conectar ao groq

import os
from dotenv import load_dotenv
from groq import Groq

#lê o arquivo ".env" (se ele existir) e coloca o que está dentro dele
#nas variáveis de ambiente do computador
#no render não existe .env: lá as variáveis vêm do painel, e o load_dotenv simplesmente não faz nada
load_dotenv()

#modelo usado se não for definido o GROQ_MODEL no .env
MODELO_PADRAO = "openai/gpt-oss-120b"

class chave_nao_configurada(Exception):
    #usado quando não achamos a chave de API
    pass

def buscar_chave():
    #busca a chave de api na variável de ambiente GROQ_API_KEY
    #se ela não existir, o getenv devolve None
    return os.getenv("GROQ_API_KEY")

def obter_modelo():
    #devolve o nome do modelo
    return os.getenv("GROQ_MODEL", MODELO_PADRAO)

def criar_cliente():
    #cria o objeto que conversa com o Groq
    chave = buscar_chave()

    if not chave:
        raise chave_nao_configurada(
            "Chave da Api do Groq não encontrada. "
            "Crie um arquivo .env com GROQ_API_KEY=sua chave"
        )

    #timeout=30 -> se o groq não responder em 30s, desistimos
    #max_retries=1 -> se der um erro passageiro, tenta mais uma vez sozinho
    return Groq(api_key=chave,
                timeout=30,
                max_retries=1)