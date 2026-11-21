#a única responsabilidade deste arquivo é descobrir quem está fazendo a requisição

import logging
import os
from dataclasses import dataclass

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from supabase import Client, create_client

logger = logging.getLogger(__name__)

#lê o cabeçalho "Authorization: Bearer <token>"
#auto_error=False: assim a resposta de erro é a nossa (401) e não a padrão do fastapi (403)
esquema = HTTPBearer(auto_error=False)


@dataclass
class UsuarioAtual:
    id: str
    #cliente do supabase que age COMO este usuário: o RLS do banco só deixa ele ver o que é dele
    banco: Client


def _nao_autorizado(mensagem: str) -> HTTPException:
    return HTTPException(
        status_code=401,
        detail=mensagem,
        headers={"WWW-Authenticate": "Bearer"},
    )


#def comum (e não async def): as chamadas ao supabase são bloqueantes,
#e assim o fastapi roda a função em outra thread sem travar as outras requisições
def usuario_atual(
    credenciais: HTTPAuthorizationCredentials | None = Depends(esquema),
) -> UsuarioAtual:
    if credenciais is None:
        raise _nao_autorizado("Faça login para continuar.")

    token = credenciais.credentials

    #um cliente novo por requisição: o cliente guarda o token, então compartilhar um só
    #entre pessoas diferentes misturaria as sessões
    banco = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_PUBLISHABLE_KEY"])

    try:
        #o supabase confere a assinatura e a validade do token e diz de quem ele é
        resposta = banco.auth.get_user(token)
    except Exception:
        logger.warning("Não foi possível validar o token", exc_info=True)
        resposta = None

    if resposta is None or resposta.user is None:
        raise _nao_autorizado("Sessão inválida ou expirada. Entre novamente.")

    #a partir daqui as consultas ao banco usam o token do usuário (o RLS passa a valer)
    banco.postgrest.auth(token)

    return UsuarioAtual(id=resposta.user.id, banco=banco)