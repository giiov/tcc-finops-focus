
# o assistente.py é o cérebro do chat:
# - recebe o histórico da conversa, chama o Groq e devolve a resposta em texto
# arquivo pensado em possível mudança futura de frame work

import groq

from src.assistente.ai.cliente import (chave_nao_configurada, criar_cliente, obter_modelo)
from src.assistente.ai.prompts import montar_prompt_sistema

# como vamos reenviar a conversa toda a cada mensagem nova para mantem a memória, uma quantidade muito grande pode esgotar os tokens muito rápido
MAX_MENSAGEM_HISTORICO = 10

MAX_TOKENS_RESPOSTA = 2000

class ErroAssistente(Exception):
    #erro com mensagem pronta
    pass

def responder(historico):
    #envia a conversa para a IA e devolve o texto da resposta

    mensagens = [
        {"role": "system", "content": montar_prompt_sistema()}
    ] + historico[-MAX_MENSAGEM_HISTORICO:]

    try:
        cliente = criar_cliente()

        resposta = cliente.chat.completions.create(
            model=obter_modelo(),
            messages=mensagens,
            #temperatura baixa = respostas mais estáveis e menos "criativas"
            #para analise de custos queremos consistência, não criatividade
            temperature=0.3,
            max_completion_tokens=MAX_TOKENS_RESPOSTA,
        )

    except chave_nao_configurada as erro:
        raise ErroAssistente(str(erro)) from erro

    #os erros abaixo vem da biblioteca do GROQ. Os mais epsecíficos vindo primeiro
    except groq.AuthenticationError as erro:
        raise ErroAssistente(
            "A chave de API do Groq foi recusada. Confira p GROQ_API_KEY no .env."
        ) from erro

    except groq.RateLimitError as erro:
        raise ErroAssistente(
            "O limite gratuito do Groq foi atingido por agora."
            "Aguarde um pouco e tente de novo!"
        ) from erro

    except (groq.NotFoundError, groq.BadRequestError) as erro:
        raise ErroAssistente(
            "O Groq recusou o pedido. O modelo pode ter sido desativado: "
            "confira o nome em GROQ_MODEL no .env e na lista de modelos do Groq."
        ) from erro

    except groq.APIConnectionError as erro:
        raise ErroAssistente(
            "Não consegui conectar ao Groq. Verifique sua internet."
        ) from erro

    except groq.APIStatusError as erro:
        raise ErroAssistente(
            f"O Groq devolveu um erro ({erro.status_code}). Tente novamente."
        ) from erro

    #a resposta vem em "choices"; pegamos o texto da primeira opção
    texto = resposta.choices[0].message.content

    #pode vir vazui se o modelos gastou todos os tokens "pensando"
    if not texto or not texto.strip():
        raise ErroAssistente(
            "A IA não conseguiu terminar a resposta. Tente reformular a pergunta :)"
        )

    return texto.strip()
