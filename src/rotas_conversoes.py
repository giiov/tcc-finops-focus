#histórico das conversões do usuário: guarda só os dados da conversão (nome, formato, linhas,
#tamanho e data). o arquivo em si não é guardado

import logging
import os
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query

from src.autenticacao import UsuarioAtual, usuario_atual

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/conversoes", tags=["conversoes"])

#mesmo limite do banco (db/006) para o nome do arquivo
TAMANHO_MAXIMO_NOME = 255


def registrar_conversao(
    usuario: UsuarioAtual,
    nome_arquivo: str | None,
    formato: str,
    total_linhas: int,
    tamanho_bytes: int,
) -> str | None:
    #grava uma linha no histórico e devolve o id dela, ou None se não conseguir gravar
    #o histórico é um extra: se o banco falhar, o usuário ainda recebe a conversão que pediu

    #o nome vem do cliente, então ficamos só com o nome do arquivo (sem pastas) e cortamos o tamanho
    nome = os.path.basename((nome_arquivo or "").replace("\\", "/")).strip() or "arquivo.csv"

    try:
        resposta = (
            usuario.banco.table("conversoes")
            .insert(
                {
                    "nome_arquivo": nome[:TAMANHO_MAXIMO_NOME],
                    "formato": formato,
                    "total_linhas": total_linhas,
                    "tamanho_bytes": tamanho_bytes,
                }
            )
            .execute()
        )
        return resposta.data[0]["id"]
    except Exception:
        logger.warning("Não foi possível gravar o histórico da conversão", exc_info=True)
        return None


@router.get("")
def listar_conversoes(
    limite: int = Query(default=50, ge=1, le=100),
    inicio: int = Query(default=0, ge=0),
    usuario: UsuarioAtual = Depends(usuario_atual),
):
    #da conversão mais recente para a mais antiga; limite e inicio permitem paginar
    #o range do supabase é inclusivo nas duas pontas
    resposta = (
        usuario.banco.table("conversoes")
        .select("id, nome_arquivo, formato, total_linhas, tamanho_bytes, criado_em")
        .order("criado_em", desc=True)
        .range(inicio, inicio + limite - 1)
        .execute()
    )
    return resposta.data


@router.delete("", status_code=204)
def limpar_historico(usuario: UsuarioAtual = Depends(usuario_atual)):
    #o filtro por user_id é explícito porque o supabase recusa um DELETE sem filtro;
    #o RLS já garantiria o mesmo resultado
    usuario.banco.table("conversoes").delete().eq("user_id", usuario.id).execute()


@router.delete("/{conversao_id}", status_code=204)
def apagar_conversao(conversao_id: UUID, usuario: UsuarioAtual = Depends(usuario_atual)):
    resposta = (
        usuario.banco.table("conversoes")
        .delete()
        .eq("id", str(conversao_id))
        .execute()
    )
    #o RLS esconde os registros dos outros: para quem pede, "não é seu" e "não existe" são iguais
    if not resposta.data:
        raise HTTPException(status_code=404, detail="Registro não encontrado.")