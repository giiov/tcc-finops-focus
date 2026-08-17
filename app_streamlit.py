import os
import streamlit as st

from src.mapping.detector import detectar_formato
from src.converters.aws_converter import converter_aws
from src.converters.gcp_converter import converter_gcp
from src.converters.azure_converter import converter_azure
from src.visualization.dashboard import gerar_graficos, calcular_kpis
from src.schemas.focus_schema import COLUNAS_OFICIAIS_FOCUS

st.set_page_config(page_title="FOCUS Multi-Cloud", layout="wide", initial_sidebar_state="expanded")

#icones em SVG (sem emoji) -- usam stroke="currentColor" pra herdar a cor do texto ao redor
ICONE_NUVEM = '<svg xmlns="http://www.w3.org/2000/svg" width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M18 10h-1.26A8 8 0 1 0 9 20h9a5 5 0 0 0 0-10z"></path></svg>'
ICONE_GRAFICO = '<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="20" x2="18" y2="10"></line><line x1="12" y1="20" x2="12" y2="4"></line><line x1="6" y1="20" x2="6" y2="14"></line></svg>'
ICONE_TABELA = '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="7" height="7"></rect><rect x="14" y="3" width="7" height="7"></rect><rect x="14" y="14" width="7" height="7"></rect><rect x="3" y="14" width="7" height="7"></rect></svg>'
ICONE_CAMADAS = '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="12 2 2 7 12 12 22 7 12 2"></polygon><polyline points="2 17 12 22 22 17"></polyline><polyline points="2 12 12 17 22 12"></polyline></svg>'
ICONE_INFO = '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line></svg>'


def _com_icone(svg, texto):
    return f'<div style="display:flex;align-items:center;gap:8px;">{svg}<span>{texto}</span></div>'


#--- identidade visual: paleta azul-marinho/ciano (cloud + dados) ---
#a base do modo escuro (cores de fundo, texto, componentes nativos) vem do
#.streamlit/config.toml -- aqui so ajustamos os elementos que criamos por conta propria
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap');

    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

    .focus-titulo {
        font-size: 2.2rem;
        font-weight: 800;
        letter-spacing: -0.03em;
        color: #e2e8f0;
        margin: 0;
    }
    .focus-titulo .destaque {
        background: linear-gradient(90deg, #38bdf8, #22d3ee);
        -webkit-background-clip: text;
        background-clip: text;
        color: transparent;
    }
    .focus-subtitulo { color: #94a3b8; font-size: 0.95rem; margin-top: 2px; }

    [data-testid="stFileUploaderDropzone"] {
        border: 1.5px dashed #1d4ed8;
        border-radius: 14px;
    }

    [data-testid="stMetric"] {
        background: #111827;
        border: 1px solid #1e293b;
        border-radius: 10px;
        padding: 12px 14px;
    }
    [data-testid="stMetricValue"] { color: #38bdf8; font-weight: 700; }

    .stTabs [data-baseweb="tab"] { font-weight: 600; }
    .stTabs [aria-selected="true"] { color: #38bdf8 !important; }

    .sidebar-explicacao {
        font-size: 0.85rem;
        color: #94a3b8;
        line-height: 1.5;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

#--- cabecalho, sempre visivel ---
st.markdown(
    f"""
    <div style="display:flex;align-items:center;gap:14px;padding:4px 0 12px;">
        <div style="color:#38bdf8;">{ICONE_NUVEM}</div>
        <div>
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
            st.markdown(_com_icone(ICONE_CAMADAS, "DATASET ATUAL"), unsafe_allow_html=True)

            provedores = df_focus["ProviderName"].dropna().unique().tolist()
            st.metric("Provedor(es)", ", ".join(provedores) if provedores else "—")
            st.metric("Registros", len(df_focus))

            st.markdown(_com_icone(ICONE_TABELA, "Colunas FOCUS disponíveis"), unsafe_allow_html=True)
            colunas_presentes = [c for c in COLUNAS_OFICIAIS_FOCUS if df_focus[c].notna().any()]
            colunas_ausentes = [c for c in COLUNAS_OFICIAIS_FOCUS if c not in colunas_presentes]
            st.caption(", ".join(colunas_presentes))
            if colunas_ausentes:
                with st.expander("Sem dado nesta fonte"):
                    st.caption(", ".join(colunas_ausentes))

        st.success(f"Formato detectado: {formato.upper()} — conversão concluída")

        #--- resumo geral (KPIs) logo no topo, antes de abrir as abas ---
        kpis = calcular_kpis(df_focus)
        col_a, col_b, col_c, col_d = st.columns(4)
        col_a.metric("Registros", kpis["registros"])
        if kpis["total_faturado"] is not None:
            col_b.metric("Total faturado", f"${kpis['total_faturado']:,.2f}")
        if kpis["total_efetivo"] is not None:
            col_c.metric("Total efetivo", f"${kpis['total_efetivo']:,.2f}")
        if kpis["economia"] is not None:
            col_d.metric("Economia", f"${kpis['economia']:,.2f}", f"{kpis['economia_pct']:.1f}%")

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