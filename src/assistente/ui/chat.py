# parte visual do assistente: bolinha no canto da tela que abre o chat

# como funciona uma bolinha flutuante no streamlit?
# 1. st.popover cria um botão que, ao clicar, abre uma janelinha
# 2. colocamos esse botão dentro de um container com um "key" (nome)
# 3. o streamlit transforma o key em uma classe CSS (.st-key-NOME), e com o CSS fixamos o container no canto da tela (position: fixed)

import streamlit as st

from src.assistente.ai.assistente import ErroAssistente, responder

CHAVE_CONTAINER = "chat_flutuante"

#icones
AVATARES = {
    "user": ":material/person:",
    "assistant": ":material/cloud:"
}

MAX_CARACTERES_PERGUNTA = 500

CSS_CHAT = """
<style>
/* Fixa o container no canto inferior direito, sempre por cima da página */
.st-key-chat_flutuante {
    position: fixed;
    bottom: 1.5rem;
    right: 1.5rem;
    z-index: 1000;
    width: auto !important;
}

/* Transforma o botão do popover em uma bolinha roxa */
.st-key-chat_flutuante button {
    width: 3.6rem;
    height: 3.6rem;
    border-radius: 50%;
    padding: 0;
    border: 1px solid rgba(230, 198, 219, 0.35);
    background: linear-gradient(135deg, #9833AF, #5F2D91);
    color: #F3E8EF;
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.45);
    transition: transform 0.18s ease, box-shadow 0.18s ease;
}
.st-key-chat_flutuante button:hover {
    transform: scale(1.06);
    box-shadow: 0 10px 30px rgba(152, 51, 175, 0.55);
    color: #FFFFFF;
}

/* O popover vem com uma setinha (expand_more) ao lado do ícone.
   Ela é a div marcada com aria-hidden: escondemos para sobrar só a bolinha */
.st-key-chat_flutuante [data-testid="stPopoverButton"] div[aria-hidden="true"] {
    display: none;
}

/* Centraliza o ícone dentro da bolinha e aumenta um pouco */
.st-key-chat_flutuante [data-testid="stPopoverButton"] > div {
    justify-content: center;
}
.st-key-chat_flutuante [data-testid="stMarkdownContainer"] p span {
    font-size: 1.6rem;
}

/* A janelinha do chat que abre ao clicar na bolinha.
   overflow-y: auto = se a tela for baixa, a janela rola em vez de cortar */
[data-testid="stPopoverBody"] {
    width: min(420px, 92vw);
    max-height: 82vh;
    overflow-y: auto;
}
</style>
"""

# perguntas prontas
SUGESTOES = [
    "O que é o padrão FOCUS?",
    "Diferença entre BilledCost e EffectiveCost?",
    "Como converterr um CSV de outro provedo?",
]

def pedir(texto):
    #chamado quando a pessoa clica numa sugestão (botão não conseguem enviar texto direto para o chat)
    st.session_state.chat_pergunta_pendente = texto

def limpar_conversa():
    st.session_state.chat_mensagens = []

def escaparr_cifrao(texto):
    #troca $ por \\$ an)tes de mostrar. No st.markdown, dois "$" no mesmo texto viram uma fórmula matemática (LaTeX) e estragam valores como "$1200 e $300". Escapando, o $ aparece normalmente.
    return texto.replace("$", "\\$")


def preparar_estado():
    #garante que o histórico da conversa exista na sessão.

    if "chat_mensagens" not in st.session_state:
        st.session_state.chat_mensagens = []


@st.fragment
def conteudo_chat():

    preparar_estado()

    mensagens = st.session_state.chat_mensagens

    #CABEÇALHO
    col_titulo, col_limpar = st.columns(
        [2, 1],
        vertical_alignment="center"
    )

    with col_titulo:
        st.markdown("**Assistente FOCUS**")

    #reserva o espaço para o botão de limpar
    with col_limpar:
        area_limpar = st.empty()

    st.caption("Tire suas dúvidas sobre FinOps, FOCUS e custos de cloud.")

    #pergunta enviada por um botão de sugestão
    pergunta_pendente = st.session_state.pop(
        "chat_pergunta_pendente", None
    )

    #SUGESTÕES
    area_sugestoes = st.empty()

    if not mensagens and not pergunta_pendente:
        with area_sugestoes.container():
            for i, texto in enumerate(SUGESTOES):
                st.button(
                    texto,
                    key=f"sugestao_{i}",
                    on_click=pedir,
                    args=(texto,),
                    use_container_width=True
                )

    #ÁREA DE MENSAGENS
    caixa = st.container(height=300, border=False)

    #CAMPO DE DIGITAÇÃO
    pergunta = st.chat_input(
        "Pergunte algo...",
        max_chars=MAX_CARACTERES_PERGUNTA,
    )

    #se clicou em uma sugestão, usa a pergunta correspondente
    pergunta = pergunta or pergunta_pendente

    with caixa:

        # Exibe o histórico anterior
        for msg in mensagens:
            with st.chat_message(
                msg["role"],
                avatar=AVATARES[msg["role"]]
            ):
                st.markdown(escaparr_cifrao(msg["content"]))

        #NOVA PERGUNTA
        if pergunta:
            area_sugestoes.empty()

            with st.chat_message(
                "user",
                avatar=AVATARES["user"]
            ):
                st.markdown(escaparr_cifrao(pergunta))

            with st.chat_message(
                "assistant",
                avatar=AVATARES["assistant"]
            ):
                try:
                    with st.spinner("Pensando..."):
                        resposta = responder(
                            mensagens + [
                                {"role": "user", "content": pergunta}
                            ]
                        )

                except ErroAssistente as erro:
                    st.error(str(erro))

                else:
                    st.markdown(escaparr_cifrao(resposta))

                    mensagens.append({
                        "role": "user",
                        "content": pergunta
                    })

                    mensagens.append({
                        "role": "assistant",
                        "content": resposta
                    })

    #RODAPÉ
    st.caption("A IA pode errar. Confira informações importantes.")

    # mostra o botão de limpar quando houver mensagens
    if mensagens:
        with area_limpar:
            st.button(
                "Limpar",
                icon=":material/delete:",
                help="Apagar a conversa",
                on_click=limpar_conversa
            )


def renderizar_chat():
    #desenha a bolinha flutuante.

    st.markdown(CSS_CHAT, unsafe_allow_html=True)

    with st.container(key=CHAVE_CONTAINER):
        with st.popover(
            ":material/forum:",
            help="Assistente FOCUS"
        ):
            conteudo_chat()
