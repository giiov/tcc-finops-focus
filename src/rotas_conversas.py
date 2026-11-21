#rotas das conversas da Ada: todas exigem login e usam o token do usuário,
#então o RLS do banco garante que cada pessoa só enxerga o que é dela

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field

from src.autenticacao import UsuarioAtual, usuario_atual

from src.assistente.ai.assistente import MAX_MENSAGEM_HISTORICO, ErroAssistente, responder

router = APIRouter(prefix="/conversas", tags=["conversas"])

#mesmo título padrão do banco (db/003): enquanto a conversa tiver ele, o título ainda não foi definido
TITULO_PADRAO = "Nova conversa"

#o título automático é o começo da primeira pergunta
TAMANHO_TITULO = 50

#mesmo limite do banco (db/004) para o texto de uma mensagem
LIMITE_CONTEUDO = 10000

#str_strip_whitespace tira os espaços das pontas antes de validar: "   " vira "" e é recusado
class NovaConversa(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    titulo: str | None = Field(default=None, min_length=1, max_length=100)


class RenomearConversa(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    titulo: str = Field(min_length=1, max_length=100)

class NovaMensagem(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    #mesmo limite da caixa de texto do front (maxLength=2000)
    content: str = Field(min_length=1, max_length=2000)
    #perfil do usuário: opcionais, pois quem não preencheu o perfil ainda pode usar o chat
    cargo: str | None = Field(default=None, max_length=100)
    provedores: list[str] | None = Field(default=None)


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
    
def _titulo_a_partir_do_texto(texto: str) -> str:
    #junta quebras de linha e espaços repetidos, e corta se for longo
    limpo = " ".join(texto.split())
    if len(limpo) <= TAMANHO_TITULO:
        return limpo
    return limpo[:TAMANHO_TITULO].rstrip() + "…"


def _buscar_conversa(usuario: UsuarioAtual, conversa_id: UUID) -> dict:
    resposta = (
        usuario.banco.table("conversas")
        .select("id, titulo")
        .eq("id", str(conversa_id))
        .execute()
    )
    if not resposta.data:
        raise HTTPException(status_code=404, detail="Conversa não encontrada.")
    return resposta.data[0]


@router.get("/{conversa_id}/mensagens")
def listar_mensagens(conversa_id: UUID, usuario: UsuarioAtual = Depends(usuario_atual)):
    _buscar_conversa(usuario, conversa_id)

    #ordenamos por id, e não por criado_em: mensagens gravadas juntas têm o mesmo horário
    resposta = (
        usuario.banco.table("mensagens")
        .select("id, role, content, criado_em")
        .eq("conversa_id", str(conversa_id))
        .order("id")
        .execute()
    )
    return resposta.data


#def comum pelo mesmo motivo do /converter: a chamada ao Groq e ao supabase é bloqueante
@router.post("/{conversa_id}/mensagens")
def enviar_mensagem(
    conversa_id: UUID,
    pedido: NovaMensagem,
    usuario: UsuarioAtual = Depends(usuario_atual),
):
    conversa = _buscar_conversa(usuario, conversa_id)

    #memória da Ada: as últimas mensagens desta conversa, lidas do banco (da mais nova para a mais
    #antiga) e depois invertidas para ficarem em ordem cronológica
    resposta = (
        usuario.banco.table("mensagens")
        .select("role, content")
        .eq("conversa_id", str(conversa_id))
        .order("id", desc=True)
        .limit(MAX_MENSAGEM_HISTORICO)
        .execute()
    )
    anteriores = list(reversed(resposta.data))

    try:
        texto = responder(
            anteriores + [{"role": "user", "content": pedido.content}],
            cargo=pedido.cargo,
            provedores=pedido.provedores,
)
    except ErroAssistente as erro:
        #as mensagens do ErroAssistente já foram escritas para o usuário ler
        raise HTTPException(status_code=503, detail=str(erro))

    #pergunta e resposta são gravadas juntas e só depois de a Ada responder: se ela falhar,
    #nada fica salvo pela metade e o usuário pode simplesmente tentar de novo
    gravadas = (
        usuario.banco.table("mensagens")
        .insert(
            [
                {"conversa_id": str(conversa_id), "role": "user", "content": pedido.content},
                {"conversa_id": str(conversa_id), "role": "assistant", "content": texto[:LIMITE_CONTEUDO]},
            ]
        )
        .execute()
    )

    #na primeira pergunta, o título da conversa passa a ser o começo dela
    titulo = conversa["titulo"]
    if not anteriores and titulo == TITULO_PADRAO:
        titulo = _titulo_a_partir_do_texto(pedido.content)
        usuario.banco.table("conversas").update({"titulo": titulo}).eq("id", str(conversa_id)).execute()

    return {
        "mensagens": sorted(gravadas.data, key=lambda m: m["id"]),
        "titulo": titulo,
    }