import base64
import html
import os
import streamlit as st # reload colors

from src.mapping.detector import detectar_formato
from src.converters.aws_converter import converter_aws
from src.converters.gcp_converter import converter_gcp
from src.converters.azure_converter import converter_azure
from src.converters.oracle_converter import converter_oracle
from src.visualization.dashboard import gerar_graficos, calcular_kpis
from src.schemas.focus_schema import COLUNAS_OFICIAIS_FOCUS

st.set_page_config(
    page_title="FOCUS Multi-Cloud",
    page_icon="src/logo_nuvem.png",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# carrega assets visuais
with open(os.path.join("src", "logo_nuvem.png"), "rb") as arquivo_logo:
    LOGO_BASE64 = base64.b64encode(arquivo_logo.read()).decode("ascii")

with open(os.path.join("src", "Trap-Black 900.otf"), "rb") as arquivo_fonte:
    FONTE_TITULO_BASE64 = base64.b64encode(arquivo_fonte.read()).decode("ascii")

ICONE_NUVEM = f'<img src="data:image/png;base64,{LOGO_BASE64}" alt="Logo FOCUS">'

# estado de sessao
if "df_focus" not in st.session_state:
    st.session_state.df_focus = None
if "formato_detectado" not in st.session_state:
    st.session_state.formato_detectado = None
if "nome_arquivo" not in st.session_state:
    st.session_state.nome_arquivo = None

# css global
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

    @font-face {
        font-family: 'Trap Black';
        src: url(data:font/otf;base64,FONTE_BASE64) format('opentype');
        font-weight: 900;
        font-style: normal;
    }

    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

    body,
    [data-testid="stAppViewContainer"] {
        background: linear-gradient(160deg, #190019 0%, #2B124C 65%, #190019 100%) !important;
        background-image: 
            linear-gradient(rgba(152, 51, 175, 0.05) 1px, transparent 1px),
            linear-gradient(90deg, rgba(152, 51, 175, 0.05) 1px, transparent 1px),
            linear-gradient(160deg, #190019 0%, #2B124C 65%, #190019 100%) !important;
        background-size: 30px 30px, 30px 30px, 100% 100% !important;
    }

    header[data-testid="stHeader"] { display: none !important; }

    [data-testid="stSidebar"],
    [data-testid="collapsedControl"],
    [data-testid="stAppDeployButton"],
    [data-testid="stMainMenu"] {
        display: none !important;
    }

    [data-testid="stAppViewContainer"] .main .block-container {
        width: 100%;
        max-width: 1280px;
        padding-top: 0;
        padding-bottom: 4rem;
        padding-left: 2.5rem;
        padding-right: 2.5rem;
    }

    .stTabs [data-baseweb="tab-list"] {
        background: rgba(20, 5, 32, 0.95);
        backdrop-filter: blur(16px);
        -webkit-backdrop-filter: blur(16px);
        border-bottom: 1px solid rgba(152, 51, 175, 0.22);
        border-radius: 0;
        gap: 0;
        padding: 0 1rem;
        position: sticky;
        top: 0;
        z-index: 100;
        margin-bottom: 0;
    }

    .stTabs [data-baseweb="tab"] {
        font-family: 'Inter', sans-serif;
        font-weight: 600;
        font-size: 0.85rem;
        letter-spacing: 0.01em;
        padding: 0.9rem 1.5rem;
        color: rgba(243, 232, 239, 0.45);
        background: transparent !important;
        transition: color 0.18s ease;
    }

    .stTabs [data-baseweb="tab"]:hover {
        color: #E6C6DB !important;
        background: transparent !important;
    }

    .stTabs [aria-selected="true"] {
        color: #9833AF !important;
        background: transparent !important;
    }

    .stTabs [data-baseweb="tab-highlight"] {
        background-color: #9833AF !important;
        height: 2px;
    }

    .stTabs [data-baseweb="tab-border"] { display: none !important; }
    .stTabs [data-baseweb="tab-panel"] { padding-top: 0 !important; }

    .focus-titulo {
        font-family: 'Trap Black', sans-serif;
        font-size: 3.5rem;
        font-weight: 900;
        letter-spacing: -0.03em;
        color: #F3E8EF;
        margin: 0;
        line-height: 1.05;
    }

    .focus-titulo .destaque {
        background: linear-gradient(90deg, #9833AF, #B24A82);
        -webkit-background-clip: text;
        background-clip: text;
        color: transparent;
    }

    .focus-subtitulo {
        color: rgba(243, 232, 239, 0.65);
        font-size: 1rem;
        margin: 0.5rem 0 0;
        line-height: 1.6;
        max-width: 560px;
    }

    .focus-icone {
        display: flex;
        align-items: center;
        justify-content: center;
        width: 5rem;
        height: 5rem;
        flex-shrink: 0;
    }

    .focus-icone img {
        width: 100%;
        height: 100%;
        object-fit: contain;
        display: block;
    }

    .hero-wrapper {
        padding: 2.5rem 0 1.5rem;
        display: flex;
        align-items: center;
        gap: 1.25rem;
    }

    .hero-texto { display: flex; flex-direction: column; }

    .fluxo-container {
        display: flex;
        align-items: stretch;
        gap: 0;
        margin: 0 0 2rem;
        flex-wrap: wrap;
    }

    .fluxo-passo {
        flex: 1;
        min-width: 130px;
        background: rgba(43, 18, 76, 0.45);
        border: 1px solid rgba(152, 51, 175, 0.18);
        border-radius: 12px;
        padding: 1.25rem 1rem 1.1rem;
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 0.35rem;
        text-align: center;
        transition: border-color 0.2s ease, background 0.2s ease;
    }

    .fluxo-passo:hover {
        border-color: rgba(152, 51, 175, 0.45);
        background: rgba(43, 18, 76, 0.65);
    }

    .fluxo-passo--destaque {
        background: rgba(95, 45, 145, 0.22);
        border-color: rgba(152, 51, 175, 0.45);
    }

    .fluxo-numero {
        font-size: 0.62rem;
        font-weight: 700;
        letter-spacing: 0.14em;
        text-transform: uppercase;
        color: rgba(230, 198, 219, 0.4);
        margin-bottom: 0.2rem;
    }

    .fluxo-label {
        font-size: 0.78rem;
        font-weight: 600;
        color: #E6C6DB;
        line-height: 1.3;
    }

    .fluxo-desc {
        font-size: 0.68rem;
        color: rgba(243, 232, 239, 0.38);
        line-height: 1.4;
        margin-top: 2px;
    }

    .fluxo-seta {
        display: flex;
        align-items: center;
        justify-content: center;
        padding: 0 0.35rem;
        color: rgba(152, 51, 175, 0.45);
        font-size: 1.1rem;
        flex-shrink: 0;
        align-self: center;
    }

    [data-testid="stFileUploaderDropzone"] {
        border: 1.5px dashed rgba(152, 51, 175, 0.55) !important;
        border-radius: 12px !important;
        background: rgba(43, 18, 76, 0.28) !important;
        transition: border-color 0.2s ease, background 0.2s ease;
        padding: 0.5rem 1rem !important;
        min-height: 0 !important;
    }

    [data-testid="stFileUploaderDropzone"]:hover {
        border-color: #9833AF !important;
        background: rgba(43, 18, 76, 0.48) !important;
    }

    [data-testid="stFileUploaderDropzoneInstructions"] {
        padding: 0.75rem 0 !important;
    }

    .upload-hint {
        font-size: 0.78rem;
        color: rgba(243, 232, 239, 0.38);
        margin-top: 0.4rem;
        line-height: 1.5;
    }

    .status-card {
        background: rgba(43, 18, 76, 0.45);
        border: 1px solid rgba(152, 51, 175, 0.28);
        border-radius: 16px;
        padding: 1.5rem 2rem;
        margin: 1.5rem 0;
    }

    .status-header {
        font-size: 0.68rem;
        font-weight: 700;
        letter-spacing: 0.1em;
        text-transform: uppercase;
        color: #2FBF71;
        margin-bottom: 1.1rem;
    }

    .status-grid {
        display: flex;
        gap: 2.5rem;
        flex-wrap: wrap;
        align-items: flex-start;
    }

    .status-item__label {
        font-size: 0.67rem;
        font-weight: 500;
        color: rgba(243, 232, 239, 0.42);
        margin-bottom: 0.2rem;
        text-transform: uppercase;
        letter-spacing: 0.07em;
    }

    .status-item__value {
        font-size: 1.65rem;
        font-weight: 700;
        color: #E6C6DB;
        line-height: 1.2;
    }

    .provider-badge {
        display: inline-flex;
        align-items: center;
        background: rgba(152, 51, 175, 0.14);
        border: 1px solid rgba(152, 51, 175, 0.38);
        border-radius: 100px;
        padding: 5px 14px;
        font-size: 0.9rem;
        font-weight: 700;
        color: #E6C6DB;
    }

    .status-divider {
        border: none;
        border-top: 1px solid rgba(152, 51, 175, 0.14);
        margin: 1.1rem 0 0.9rem;
    }

    .status-nav-hint {
        font-size: 0.8rem;
        color: rgba(243, 232, 239, 0.4);
        margin: 0;
        line-height: 1.5;
    }

    .secao-header {
        display: flex;
        align-items: center;
        gap: 8px;
        margin: 2rem 0 0.75rem;
        padding-bottom: 0.55rem;
        border-bottom: 1px solid rgba(152, 51, 175, 0.18);
    }

    .secao-header__titulo {
        font-size: 0.72rem;
        font-weight: 700;
        letter-spacing: 0.1em;
        text-transform: uppercase;
        color: rgba(243, 232, 239, 0.5);
    }

    .input-info-grid {
        display: flex;
        gap: 2rem;
        flex-wrap: wrap;
        padding: 1rem 1.4rem;
        background: rgba(43, 18, 76, 0.35);
        border: 1px solid rgba(152, 51, 175, 0.18);
        border-radius: 12px;
        margin-bottom: 1.5rem;
    }

    .input-info-item__label {
        font-size: 0.67rem;
        color: rgba(243, 232, 239, 0.4);
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.07em;
        margin-bottom: 2px;
    }

    .input-info-item__value {
        font-size: 0.92rem;
        font-weight: 600;
        color: #E6C6DB;
    }

    .focus-columns-list {
        list-style: none;
        margin: 0.5rem 0 1rem;
        padding: 0;
        display: flex;
        flex-wrap: wrap;
        gap: 6px;
    }

    .focus-columns-list li {
        display: inline-block;
        background: rgba(95, 45, 145, 0.18);
        border: 1px solid rgba(152, 51, 175, 0.28);
        border-radius: 6px;
        padding: 3px 10px;
        font-size: 0.72rem;
        font-weight: 500;
        color: #E6C6DB;
        word-break: break-word;
        white-space: normal;
    }

    .focus-columns-list li.missing {
        background: rgba(243, 232, 239, 0.03);
        border-color: rgba(243, 232, 239, 0.08);
        color: rgba(243, 232, 239, 0.25);
    }

    [data-testid="stMetric"] {
        background: rgba(43, 18, 76, 0.5);
        border: 1px solid rgba(152, 51, 175, 0.22);
        border-radius: 14px;
        padding: 1rem 1.25rem;
        transition: border-color 0.18s ease, transform 0.18s ease;
    }

    [data-testid="stMetric"]:hover {
        border-color: rgba(152, 51, 175, 0.55);
        transform: translateY(-2px);
    }

    [data-testid="stMetricValue"] { color: #E6C6DB; font-weight: 700; }
    [data-testid="stMetricLabel"] { color: rgba(243, 232, 239, 0.55) !important; }

    [data-testid="stPlotlyChart"] {
        background: rgba(15, 5, 25, 0.65);
        border: 1px solid rgba(152, 51, 175, 0.25);
        border-radius: 18px;
        padding: 0.5rem;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.4);
        height: 100%;
        transition: transform 0.2s ease, box-shadow 0.2s ease, border-color 0.2s ease;
    }

    [data-testid="stPlotlyChart"]:hover {
        transform: translateY(-2px);
        box-shadow: 0 14px 40px rgba(0, 0, 0, 0.6);
        border-color: rgba(152, 51, 175, 0.45);
    }

    .viz-intro {
        font-size: 0.85rem;
        color: rgba(243, 232, 239, 0.45);
        margin: 0.25rem 0 1.5rem;
        line-height: 1.6;
    }

    .sobre-card {
        background: rgba(43, 18, 76, 0.38);
        border: 1px solid rgba(152, 51, 175, 0.18);
        border-radius: 14px;
        padding: 1.5rem 1.75rem;
        margin-bottom: 1rem;
    }

    .sobre-card__titulo {
        font-size: 0.68rem;
        font-weight: 700;
        letter-spacing: 0.1em;
        text-transform: uppercase;
        color: #9833AF;
        margin-bottom: 0.75rem;
    }

    .sobre-card__texto {
        font-size: 0.9rem;
        color: rgba(243, 232, 239, 0.75);
        line-height: 1.75;
        margin: 0;
    }

    .provider-tag {
        display: inline-block;
        background: rgba(43, 18, 76, 0.6);
        border: 1px solid rgba(152, 51, 175, 0.28);
        border-radius: 8px;
        padding: 6px 16px;
        font-size: 0.85rem;
        font-weight: 600;
        color: #E6C6DB;
        margin: 3px;
    }

    .tech-tag {
        display: inline-block;
        background: rgba(95, 45, 145, 0.14);
        border: 1px solid rgba(152, 51, 175, 0.22);
        border-radius: 6px;
        padding: 4px 12px;
        font-size: 0.82rem;
        font-weight: 500;
        color: rgba(243, 232, 239, 0.65);
        margin: 3px;
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
    </style>
    """.replace("FONTE_BASE64", FONTE_TITULO_BASE64),
    unsafe_allow_html=True,
)


# hero principal no topo da pagina (fora das abas)
st.markdown(
    f"""
    <div class="hero-wrapper" style="padding: 1rem 0 1.5rem;">
        <div class="focus-icone">{ICONE_NUVEM}</div>
        <div class="hero-texto">
            <p class="focus-titulo"><span class="destaque">FOCUS</span> Multi&#8209;Cloud</p>
            <p class="focus-subtitulo">
                Padronização e análise de custos AWS, GCP, Azure e Oracle em um único padrão.
            </p>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# navegacao
aba_inicio, aba_dados, aba_viz, aba_sobre = st.tabs([
    ":material/home: Início",
    ":material/table_chart: Dados",
    ":material/bar_chart: Visualizações",
    ":material/info: Sobre",
])


# ── ABA INÍCIO ────────────────────────────────────────────────────────────────
with aba_inicio:

    # upload
    st.markdown("##### :material/upload_file: Envie seu arquivo de custos (.csv)")
    arquivo_enviado = st.file_uploader(
        "Envie seu arquivo de custos (.csv)",
        type=["csv"],
        label_visibility="collapsed",
    )
    st.markdown(
        '<p class="upload-hint">Suportados: AWS Cost and Usage Report &nbsp;·&nbsp; GCP Billing Export &nbsp;·&nbsp; Azure Cost Export &nbsp;·&nbsp; Oracle OCI Cost</p>',
        unsafe_allow_html=True,
    )

    # processamento do arquivo
    if arquivo_enviado is not None:

        caminho_arquivo = os.path.join("data", "input", arquivo_enviado.name)
        os.makedirs(os.path.dirname(caminho_arquivo), exist_ok=True)
        with open(caminho_arquivo, "wb") as f:
            f.write(arquivo_enviado.getbuffer())

        # reprocessa
        if st.session_state.nome_arquivo != arquivo_enviado.name:
            try:
                formato = detectar_formato(caminho_arquivo)

                if formato == "gcp":
                    df_focus = converter_gcp(caminho_arquivo)
                elif formato == "aws":
                    df_focus = converter_aws(caminho_arquivo)
                elif formato == "azure":
                    df_focus = converter_azure(caminho_arquivo)
                elif formato == "oracle":
                    df_focus = converter_oracle(caminho_arquivo)

                st.session_state.df_focus = df_focus
                st.session_state.formato_detectado = formato
                st.session_state.nome_arquivo = arquivo_enviado.name

            except Exception as erro:
                st.error(f"Erro durante a conversão: {erro}")

    if st.session_state.df_focus is not None:
        # pos-upload
        df = st.session_state.df_focus
        formato = st.session_state.formato_detectado
        nome = st.session_state.nome_arquivo

        provedores = df["ServiceProviderName"].dropna().unique().tolist()
        provider_display = html.escape(", ".join(provedores)) if provedores else formato.upper()
        colunas_presentes = [c for c in COLUNAS_OFICIAIS_FOCUS if c in df.columns and df[c].notna().any()]

        st.markdown(
            f"""
            <div class="status-card">
                <div class="status-header">&#10003;&ensp;Arquivo processado com sucesso</div>
                <div class="status-grid">
                    <div>
                        <div class="status-item__label">Provedor</div>
                        <div class="provider-badge">{provider_display}</div>
                    </div>
                    <div>
                        <div class="status-item__label">Registros</div>
                        <div class="status-item__value">{len(df):,}</div>
                    </div>
                    <div>
                        <div class="status-item__label">Colunas FOCUS</div>
                        <div class="status-item__value">
                            {len(colunas_presentes)}<span style="font-size:0.9rem;color:rgba(243,232,239,0.35);font-weight:400;"> / {len(COLUNAS_OFICIAIS_FOCUS)}</span>
                        </div>
                    </div>
                    <div>
                        <div class="status-item__label">Arquivo</div>
                        <div class="status-item__value" style="font-size:0.85rem;color:rgba(243,232,239,0.55);font-weight:500;word-break:break-all;">{html.escape(nome)}</div>
                    </div>
                </div>
                <hr class="status-divider">
                <p class="status-nav-hint">
                    Navegue pelas abas <strong style="color:#E6C6DB;">Dados</strong> e <strong style="color:#E6C6DB;">Visualizações</strong> para explorar os resultados.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    else:
        # pre-upload
        st.markdown(
            """
            <div class="fluxo-container">
                <div class="fluxo-passo">
                    <div class="fluxo-numero">01</div>
                    <div class="fluxo-label">Arquivo de Entrada</div>
                    <div class="fluxo-desc">CSV de custos do provedor cloud</div>
                </div>
                <div class="fluxo-seta">&#8594;</div>
                <div class="fluxo-passo">
                    <div class="fluxo-numero">02</div>
                    <div class="fluxo-label">Detecção do Provedor</div>
                    <div class="fluxo-desc">Identificação automática por colunas</div>
                </div>
                <div class="fluxo-seta">&#8594;</div>
                <div class="fluxo-passo">
                    <div class="fluxo-numero">03</div>
                    <div class="fluxo-label">Padronização</div>
                    <div class="fluxo-desc">Mapeamento e conversão para FOCUS</div>
                </div>
                <div class="fluxo-seta">&#8594;</div>
                <div class="fluxo-passo fluxo-passo--destaque">
                    <div class="fluxo-numero">04</div>
                    <div class="fluxo-label">Resultado FOCUS</div>
                    <div class="fluxo-desc">Estrutura padronizada, pronta para análise</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


# ── ABA DADOS ─────────────────────────────────────────────────────────────────
with aba_dados:

    if st.session_state.df_focus is None:
        st.info(":material/upload_file: Envie um arquivo na aba **Início** para visualizar os dados.")
    else:
        df = st.session_state.df_focus
        formato = st.session_state.formato_detectado
        nome = st.session_state.nome_arquivo

        provedores = df["ServiceProviderName"].dropna().unique().tolist()
        provider_display = html.escape(", ".join(provedores)) if provedores else formato.upper()
        colunas_presentes = [c for c in COLUNAS_OFICIAIS_FOCUS if c in df.columns and df[c].notna().any()]
        colunas_ausentes = [c for c in COLUNAS_OFICIAIS_FOCUS if c not in colunas_presentes]

        # arquivo de entrada
        st.markdown(
            '<div class="secao-header"><span class="secao-header__titulo">Arquivo de Entrada</span></div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            f"""
            <div class="input-info-grid">
                <div>
                    <div class="input-info-item__label">Arquivo</div>
                    <div class="input-info-item__value">{html.escape(nome)}</div>
                </div>
                <div>
                    <div class="input-info-item__label">Provedor detectado</div>
                    <div class="input-info-item__value">{provider_display}</div>
                </div>
                <div>
                    <div class="input-info-item__label">Registros convertidos</div>
                    <div class="input-info-item__value">{len(df):,}</div>
                </div>
                <div>
                    <div class="input-info-item__label">Colunas FOCUS preenchidas</div>
                    <div class="input-info-item__value">{len(colunas_presentes)} / {len(COLUNAS_OFICIAIS_FOCUS)}</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # tabela padronizada
        st.markdown(
            '<div class="secao-header" style="margin-top:2rem;"><span class="secao-header__titulo">Dados padronizados FOCUS</span></div>',
            unsafe_allow_html=True,
        )
        st.dataframe(df, use_container_width=True)

        csv_bytes = df.to_csv(index=False).encode("utf-8")
        st.download_button(
            "Baixar CSV padronizado",
            data=csv_bytes,
            file_name="focus_padronizado.csv",
            mime="text/csv",
        )

        # colunas presentes
        st.markdown(":material/check_circle: **Colunas FOCUS disponíveis neste arquivo**")
        itens_presentes = "".join(f"<li>{html.escape(col)}</li>" for col in colunas_presentes)
        st.markdown(
            f'<ul class="focus-columns-list">{itens_presentes}</ul>',
            unsafe_allow_html=True,
        )

        if colunas_ausentes:
            with st.expander("Colunas sem dado nesta fonte"):
                itens_ausentes = "".join(f"<li class='missing'>{html.escape(col)}</li>" for col in colunas_ausentes)
                st.markdown(
                    f'<ul class="focus-columns-list">{itens_ausentes}</ul>',
                    unsafe_allow_html=True,
                )


# ── ABA VISUALIZAÇÕES ─────────────────────────────────────────────────────────
with aba_viz:

    if st.session_state.df_focus is None:
        st.info(":material/upload_file: Envie um arquivo na aba **Início** para ver as visualizações.")
    else:
        df = st.session_state.df_focus

        # kpis
        kpis = calcular_kpis(df)
        col_efetivo, col_faturado, col_economia = st.columns([2.5, 1.25, 1.25])

        if kpis["total_efetivo"] is not None:
            col_efetivo.metric("Total efetivo", f"${kpis['total_efetivo']:,.2f}")
        if kpis["total_faturado"] is not None:
            col_faturado.metric("Total faturado", f"${kpis['total_faturado']:,.2f}")
        if kpis["economia"] is not None:
            col_economia.metric("Economia", f"${kpis['economia']:,.2f}")

        st.markdown(
            '<p class="viz-intro">Visualizações geradas automaticamente a partir das colunas disponíveis no arquivo convertido.</p>',
            unsafe_allow_html=True,
        )

        # graficos
        graficos = gerar_graficos(df)

        if not graficos:
            st.info("Não há dados suficientes neste arquivo para gerar visualizações.")
        else:
            # O grafico temporal ganha destaque ocupando a largura total
            if "tempo" in graficos:
                st.plotly_chart(graficos.pop("tempo"), use_container_width=True)
                st.markdown("<br>", unsafe_allow_html=True) # Espaco sutil

            # Os demais graficos sao dispostos em um grid estruturado de 2 colunas
            figuras_restantes = list(graficos.values())
            for i in range(0, len(figuras_restantes), 2):
                par = figuras_restantes[i:i + 2]
                colunas_layout = st.columns(len(par))
                for coluna_layout, fig in zip(colunas_layout, par):
                    coluna_layout.plotly_chart(fig, use_container_width=True)


# ── ABA SOBRE ─────────────────────────────────────────────────────────────────
with aba_sobre:

    col_sobre_logo, col_sobre_texto = st.columns([1, 9], gap="small")
    with col_sobre_logo:
        st.markdown(
            f'<div class="focus-icone" style="margin-top:1.5rem;">{ICONE_NUVEM}</div>',
            unsafe_allow_html=True,
        )

    with col_sobre_texto:
        st.markdown(
            """
            <div style="padding: 1.5rem 0 2rem;">
                <p class="focus-titulo" style="font-size:2.4rem;">
                    <span class="destaque">FOCUS</span> Multi&#8209;Cloud
                </p>
                <p class="focus-subtitulo">Ferramenta de TCC para padronização de custos cloud</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    col_esq, col_dir = st.columns([3, 2], gap="large")

    with col_esq:
        st.markdown(
            """
            <div class="sobre-card">
                <div class="sobre-card__titulo">O que é o FOCUS Multi-Cloud?</div>
                <p class="sobre-card__texto">
                    O FOCUS Multi-Cloud é uma ferramenta desenvolvida como Trabalho de Conclusão de Curso (TCC)
                    que recebe arquivos de custos de diferentes provedores de nuvem, identifica automaticamente
                    o formato de origem e converte os dados para o padrão FOCUS — permitindo comparar e analisar
                    gastos multi-cloud em uma estrutura única e consistente.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown(
            """
            <div class="sobre-card">
                <div class="sobre-card__titulo">O padrão FOCUS</div>
                <p class="sobre-card__texto">
                    <strong style="color:#E6C6DB;">FOCUS</strong> (FinOps Open Cost and Usage Specification)
                    é um padrão aberto mantido pela FinOps Foundation que define um esquema comum para dados
                    de custo e uso de serviços cloud. O objetivo é eliminar as diferenças de nomenclatura e
                    estrutura entre provedores, permitindo que times de FinOps analisem custos multi-cloud
                    de forma direta e comparável.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown(
            """
            <div class="sobre-card">
                <div class="sobre-card__titulo">Objetivo do projeto</div>
                <p class="sobre-card__texto">
                    Demonstrar como a adoção do padrão FOCUS pode simplificar a análise de custos em ambientes
                    multi-cloud, reduzindo o esforço manual de normalização de dados e possibilitando uma visão
                    unificada dos gastos independentemente do provedor utilizado.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col_dir:
        st.markdown(
            """
            <div class="sobre-card">
                <div class="sobre-card__titulo">Provedores suportados</div>
                <div style="display:flex;flex-wrap:wrap;gap:6px;margin-top:0.25rem;">
                    <span class="provider-tag">AWS</span>
                    <span class="provider-tag">Microsoft Azure</span>
                    <span class="provider-tag">Google Cloud</span>
                    <span class="provider-tag">Oracle Cloud</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown(
            """
            <div class="sobre-card">
                <div class="sobre-card__titulo">Tecnologias utilizadas</div>
                <div style="margin-top:0.25rem;">
                    <span class="tech-tag">Python</span>
                    <span class="tech-tag">Streamlit</span>
                    <span class="tech-tag">Pandas</span>
                    <span class="tech-tag">Plotly</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown(
            """
            <div class="sobre-card">
                <div class="sobre-card__titulo">Como usar</div>
                <p class="sobre-card__texto" style="font-size:0.85rem;">
                    1. Acesse a aba <strong style="color:#E6C6DB;">Início</strong><br>
                    2. Envie um arquivo CSV de custos cloud<br>
                    3. O sistema detecta o provedor automaticamente<br>
                    4. Explore os dados na aba <strong style="color:#E6C6DB;">Dados</strong><br>
                    5. Visualize os gráficos em <strong style="color:#E6C6DB;">Visualizações</strong>
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )