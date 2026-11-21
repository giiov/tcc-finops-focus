#rotas das conversas da Ada: todas exigem login e usam o token do usuário,
#então o RLS do banco garante que cada pessoa só enxerga o que é dela

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field

from src.autenticacao import UsuarioAtual, usuario_atual

router = APIRouter(prefix="/conversas", tags=["conversas"])

#mesmo título padrão do banco (db/003): enquanto a conversa tiver ele, o título ainda não foi definido
TITULO_PADRAO = "Nova conversa"


#str_strip_whitespace tira os espaços das pontas antes de validar: "   " vira "" e é recusado
class NovaConversa(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    titulo: str | None = Field(default=None, min_length=1, max_length=100)


class RenomearConversa(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    titulo: str = Field(min_length=1, max_length=100)


@router.get("")
def listar_conversas(usuario: UsuarioAtual = Depends(usuario_atual)):
    #lista lateral: da conversa com atividade mais recente para a mais antiga
    resposta = (
        usuario.banco.table("conversas")
        .select("id, titulo, criado_em, atualizado_em")
        .order("atualizado_em", desc=True)
        .execute()
    )
    return resposta.data


@router.post("", status_code=201)
def criar_conversa(
    pedido: NovaConversa | None = None,
    usuario: UsuarioAtual = Depends(usuario_atual),
):
    titulo = (pedido.titulo if pedido else None) or TITULO_PADRAO
    resposta = usuario.banco.table("conversas").insert({"titulo": titulo}).execute()
    return resposta.data[0]


@router.patch("/{conversa_id}")
def renomear_conversa(
    conversa_id: UUID,
    pedido: RenomearConversa,
    usuario: UsuarioAtual = Depends(usuario_atual),
):
    resposta = (
        usuario.banco.table("conversas")
        .update({"titulo": pedido.titulo})
        .eq("id", str(conversa_id))
        .execute()
    )
    #o RLS esconde as conversas dos outros: para quem pede, "não é sua" e "não existe" são iguais
    if not resposta.data:
        raise HTTPException(status_code=404, detail="Conversa não encontrada.")
    return resposta.data[0]


@router.delete("/{conversa_id}", status_code=204)
def apagar_conversa(conversa_id: UUID, usuario: UsuarioAtual = Depends(usuario_atual)):
    #as mensagens da conversa são apagadas junto (on delete cascade no banco)
    resposta = (
        usuario.banco.table("conversas")
        .delete()
        .eq("id", str(conversa_id))
        .execute()
    )
    if not resposta.data:
        raise HTTPException(status_code=404, detail="Conversa não encontrada.")