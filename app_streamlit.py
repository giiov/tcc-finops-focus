import base64
import html
import os
import streamlit as st
import streamlit.components.v1 as components

from src.mapping.detector import detectar_formato
from src.converters.aws_converter import converter_aws
from src.converters.gcp_converter import converter_gcp
from src.converters.azure_converter import converter_azure
from src.visualization.dashboard import gerar_graficos, calcular_kpis
from src.schemas.focus_schema import COLUNAS_OFICIAIS_FOCUS

st.set_page_config(page_title="FOCUS Multi-Cloud", layout="wide", initial_sidebar_state="expanded")

#icones em SVG (sem emoji) -- usam stroke="currentColor" pra herdar a cor do texto ao redor
with open(os.path.join("src", "logo.png"), "rb") as arquivo_logo:
    LOGO_BASE64 = base64.b64encode(arquivo_logo.read()).decode("ascii")

ICONE_NUVEM = f'<img src="data:image/png;base64,{LOGO_BASE64}" alt="Logo FOCUS">'
ICONE_GRAFICO = '<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="20" x2="18" y2="10"></line><line x1="12" y1="20" x2="12" y2="4"></line><line x1="6" y1="20" x2="6" y2="14"></line></svg>'
ICONE_TABELA = '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="7" height="7"></rect><rect x="14" y="3" width="7" height="7"></rect><rect x="14" y="14" width="7" height="7"></rect><rect x="3" y="14" width="7" height="7"></rect></svg>'
ICONE_CAMADAS = '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="12 2 2 7 12 12 22 7 12 2"></polygon><polyline points="2 17 12 22 22 17"></polyline><polyline points="2 12 12 17 22 12"></polyline></svg>'
ICONE_INFO = '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line></svg>'


def _com_icone(svg, texto):
    return f'<div style="display:flex;align-items:center;gap:8px;">{svg}<span>{texto}</span></div>'


#--- identidade visual: paleta ameixa/rosa (cloud + dados) ---
#a base do modo escuro (cores de fundo, texto, componentes nativos) vem do
#.streamlit/config.toml -- aqui so ajustamos os elementos que criamos por conta propria
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap');

    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

    body,
    [data-testid="stAppViewContainer"] {
        background: linear-gradient(0deg, #190019 0%, #2b124c 100%);
    }

    .focus-titulo {
        font-size: 3rem !important;
        font-weight: 800;
        letter-spacing: -0.03em;
        color: #f3e8ef;
        margin: 0;
        line-height: 1.1;
    }
    .focus-titulo .destaque {
        background: linear-gradient(90deg, #9833af, #b24a82);
        -webkit-background-clip: text;
        background-clip: text;
        color: transparent;
    }
    .focus-subtitulo {
        color: #f3e8ef;
        font-size: 0.95rem;
        margin: 2px 0 0 0;
    }
    .focus-icone {
        display: flex;
        align-items: flex-start;
        justify-content: center;
        width: 4.5rem;
        height: 4.5rem;
        color: #d47fa3;
        flex-shrink: 0;
        margin-top: -0.5rem;
    }
    .focus-icone svg {
        width: 100%;
        height: 100%;
        display: block;
    }
    .focus-icone img {
        width: 100%;
        height: 100%;
        object-fit: contain;
        display: block;
    }
    .focus-texto {
        display: flex;
        flex-direction: column;
        justify-content: flex-start;
        align-items: flex-start;
        gap: 0;
    }

    [data-testid="stFileUploaderDropzone"] {
        border: 1.5px dashed #b24a82;
        border-radius: 14px;
    }

    [data-testid="stDownloadButton"] button {
        display: inline-flex;
        align-items: center;
        gap: 8px;
    }
    [data-testid="stDownloadButton"] button::before {
        content: "";
        width: 16px;
        height: 16px;
        flex: 0 0 16px;
        background-color: currentColor;
        -webkit-mask: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='black' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M12 3v12'/%3E%3Cpath d='m7 10 5 5 5-5'/%3E%3Cpath d='M5 21h14'/%3E%3C/svg%3E") center / 16px 16px no-repeat;
        mask: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='black' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M12 3v12'/%3E%3Cpath d='m7 10 5 5 5-5'/%3E%3Cpath d='M5 21h14'/%3E%3C/svg%3E") center / 16px 16px no-repeat;
    }

    [data-testid="stMetric"] {
        background: #2d2b2e;
        border: 1px solid rgba(181, 169, 176, 0.42);
        border-radius: 14px;
        padding: 12px 14px;
        box-shadow: 0 0 0 rgba(212, 127, 163, 0);
        transition: box-shadow 0.18s ease, border-color 0.18s ease, transform 0.18s ease;
    }
    [data-testid="stMetric"]:hover {
        box-shadow: 0 0.75rem 1.5rem rgba(212, 127, 163, 0.14);
        border-color: rgba(212, 127, 163, 0.8);
        transform: translateY(-2px);
    }
    [data-testid="stMetricValue"] { color: #d47fa3; font-weight: 700; }

    [data-testid="stHorizontalBlock"] > div:nth-child(1) [data-testid="stMetric"] {
        background: #2c3032;
        border-color: rgba(157, 174, 177, 0.58);
    }
    [data-testid="stHorizontalBlock"] > div:nth-child(1) [data-testid="stMetricValue"] {
        color: #8fb6c6;
    }
    [data-testid="stHorizontalBlock"] > div:nth-child(2) [data-testid="stMetric"] {
        background: #33312d;
        border-color: rgba(187, 171, 137, 0.58);
    }
    [data-testid="stHorizontalBlock"] > div:nth-child(2) [data-testid="stMetricValue"] {
        color: #d2b276;
    }
    [data-testid="stHorizontalBlock"] > div:nth-child(3) [data-testid="stMetric"] {
        background: #2d322f;
        border-color: rgba(146, 173, 157, 0.58);
    }
    [data-testid="stHorizontalBlock"] > div:nth-child(3) [data-testid="stMetricValue"] {
        color: #91bd9f;
    }

    .stTabs [data-baseweb="tab"] { font-weight: 600; }
    .stTabs [aria-selected="true"] { color: #d47fa3 !important; }

    .sidebar-explicacao {
        font-size: 0.85rem;
        color: #d0c9cd;
        line-height: 1.5;
        margin: 0;
    }

    .sidebar-card {
        background: #2d2b2e;
        border: 1px solid rgba(181, 169, 176, 0.42);
        border-radius: 14px;
        padding: 12px 14px;
        margin: 0 0 10px;
        box-shadow: 0 0 0 rgba(212, 127, 163, 0);
        transition: box-shadow 0.18s ease, border-color 0.18s ease, transform 0.18s ease;
    }
    .sidebar-card:hover {
        box-shadow: 0 0.75rem 1.5rem rgba(212, 127, 163, 0.14);
        border-color: rgba(212, 127, 163, 0.8);
        transform: translateY(-2px);
    }
    .sidebar-card--compact {
        padding: 12px 14px;
    }
    .sidebar-card--provider {
        background: #302f32;
        border-color: rgba(177, 171, 183, 0.56);
    }
    .sidebar-card--provider .sidebar-card__value {
        color: #b6a7d0;
    }
    .sidebar-card--records {
        background: #33312d;
        border-color: rgba(187, 171, 137, 0.58);
    }
    .sidebar-card--records .sidebar-card__value {
        color: #d2b276;
    }
    .sidebar-card__label {
        font-size: 0.875rem;
        font-weight: 400;
        letter-spacing: normal;
        color: rgba(231, 225, 228, 0.7);
        margin-bottom: 0.25rem;
    }
    .sidebar-card__value {
        font-size: 1.75rem;
        line-height: 1.2;
        font-weight: 700;
        color: #d47fa3;
        word-break: break-word;
    }
    .sidebar-section-title {
        margin-bottom: 12px;
    }
    .focus-columns-list {
        list-style: disc;
        margin: 12px 0;
        padding-left: 1.1rem;
        column-count: 2;
        column-gap: 1.2rem;
        width: 100%;
        text-align: left;
        align-items: flex-start;
        justify-content: flex-start;
    }
    .focus-columns-list li {
        display: list-item;
        break-inside: avoid;
        margin: 0 0 0.35rem;
        padding: 0;
        background: transparent;
        border: none;
        border-radius: 0;
        color: #f3e8ef;
        font-size: 0.74rem;
        line-height: 1.3;
        white-space: normal;
        text-align: left;
    }
    .focus-columns-list li.missing {
        background: transparent;
        border: none;
        color: #d0c9cd;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

#--- cabecalho, sempre visivel ---
st.markdown(
    f"""
    <div style="display:flex;align-items:flex-start;gap:14px;padding:4px 0 12px;">
        <div class="focus-icone">{ICONE_NUVEM}</div>
        <div class="focus-texto">
            <p class="focus-titulo"><span class="destaque">FOCUS</span> Multi-Cloud</p>
            <p class="focus-subtitulo">Padronização e análise de custos AWS, GCP e Azure em um único padrão</p>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

#--- sidebar: acessivel desde o inicio, com explicacao fixa do projeto ---
with st.sidebar:
    st.markdown(_com_icone(ICONE_INFO, "SOBRE O PROJETO"), unsafe_allow_html=True)
    st.markdown(
        """
        <p class="sidebar-explicacao">
        Ferramenta de TCC que recebe arquivos de custo de diferentes provedores de nuvem
        (AWS, GCP, Azure), identifica automaticamente a origem e converte os dados para o
        padrão <b>FOCUS</b> (FinOps Open Cost and Usage Specification) — permitindo comparar
        e analisar custos multi-cloud em uma estrutura única.
        </p>
        """,
        unsafe_allow_html=True,
    )
    st.divider()

    #placeholder do dataset, preenchido mais abaixo se um arquivo for enviado
    secao_dataset = st.container()

arquivo_enviado = st.file_uploader("Envie seu arquivo de custos (.csv)", type=["csv"])

if arquivo_enviado is not None:

    #salva o arquivo recebido dentro de data/input
    caminho_arquivo = os.path.join("data", "input", arquivo_enviado.name)
    os.makedirs(os.path.dirname(caminho_arquivo), exist_ok=True)
    with open(caminho_arquivo, "wb") as f:
        f.write(arquivo_enviado.getbuffer())

    try:
        #detecta o formato automaticamente
        formato = detectar_formato(caminho_arquivo)

        #escolhe o converter certo
        if formato == "gcp":
            df_focus = converter_gcp(caminho_arquivo)
        elif formato == "aws":
            df_focus = converter_aws(caminho_arquivo)
        elif formato == "azure":
            df_focus = converter_azure(caminho_arquivo)

        #--- preenche a secao de dataset na sidebar, criada mais acima ---
        with secao_dataset:
            st.markdown(
                f'<div class="sidebar-section-title">{_com_icone(ICONE_CAMADAS, "DATASET ATUAL")}</div>',
                unsafe_allow_html=True,
            )

            provedores = df_focus["ProviderName"].dropna().unique().tolist()
            provider_value = html.escape(", ".join(provedores)) if provedores else "—"
            st.markdown(
                f"""
                <div class="sidebar-card sidebar-card--compact sidebar-card--provider">
                    <div class="sidebar-card__label">Provedor(es)</div>
                    <div class="sidebar-card__value">{provider_value}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            st.markdown(
                f"""
                <div class="sidebar-card sidebar-card--compact sidebar-card--records">
                    <div class="sidebar-card__label">Registros</div>
                    <div class="sidebar-card__value">{len(df_focus):,}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            st.markdown(_com_icone(ICONE_TABELA, "Colunas FOCUS disponíveis"), unsafe_allow_html=True)
            colunas_presentes = [c for c in COLUNAS_OFICIAIS_FOCUS if df_focus[c].notna().any()]
            colunas_ausentes = [c for c in COLUNAS_OFICIAIS_FOCUS if c not in colunas_presentes]

            itens_presentes = "".join(f"<li>{html.escape(col)}</li>" for col in colunas_presentes)
            st.markdown(
                f"""
                <ul class="focus-columns-list">{itens_presentes}</ul>
                """,
                unsafe_allow_html=True,
            )

            if colunas_ausentes:
                with st.expander("Sem dado nesta fonte"):
                    itens_ausentes = "".join(f"<li class='missing'>{html.escape(col)}</li>" for col in colunas_ausentes)
                    st.markdown(
                        f"""
                        <ul class="focus-columns-list">{itens_ausentes}</ul>
                        """,
                        unsafe_allow_html=True,
                    )

        # Os calculos dos KPIs sao mantidos para uso futuro; os cards exibem apenas os valores.
        kpis = calcular_kpis(df_focus)
        col_efetivo, col_faturado, col_economia = st.columns([2.5, 1.25, 1.25])

        if kpis["total_efetivo"] is not None:
            col_efetivo.metric("Total efetivo", f"${kpis['total_efetivo']:,.2f}")
        if kpis["total_faturado"] is not None:
            col_faturado.metric("Total faturado", f"${kpis['total_faturado']:,.2f}")
        if kpis["economia"] is not None:
            col_economia.metric("Economia", f"${kpis['economia']:,.2f}")

        aba_dados, aba_graficos = st.tabs(["Dados", "Visualizações"])

        with aba_dados:
            st.dataframe(df_focus, use_container_width=True)
            csv_bytes = df_focus.to_csv(index=False).encode("utf-8")
            st.download_button(
                "Baixar CSV padronizado",
                data=csv_bytes,
                file_name="focus_padronizado.csv",
                mime="text/csv",
            )

        with aba_graficos:
            st.markdown(_com_icone(ICONE_GRAFICO, "Visualizações geradas a partir das colunas disponíveis"), unsafe_allow_html=True)
            graficos = gerar_graficos(df_focus)

            if not graficos:
                st.info("Não há dados suficientes neste arquivo para gerar visualizações.")
            else:
                for i in range(0, len(graficos), 2):
                    par = graficos[i:i + 2]
                    colunas_layout = st.columns(len(par))
                    for coluna_layout, fig in zip(colunas_layout, par):
                        coluna_layout.plotly_chart(fig, use_container_width=True)

    except Exception as erro:
        st.error(f"Erro durante a conversão: {erro}")

else:
    with secao_dataset:
        st.caption("Envie um arquivo para ver os detalhes do dataset aqui.")