import os
import streamlit as st

from src.mapping.detector import detectar_formato
from src.converters.aws_converter import converter_aws
from src.converters.gcp_converter import converter_gcp
from src.converters.azure_converter import converter_azure
from src.visualization.dashboard import grafico_custos_por_servico

st.title("Conversor de Custos Cloud -> FOCUS")

#componente de upload - só aceita CSV por enquanto
arquivo_enviado = st.file_uploader("Envie seu arquivo de custos csv", type=["csv"])

#só executa o fluxo se algum arquivo tiver sido enviado
if arquivo_enviado is not None:

    #salva o arquivo recebido dentro de data/input
    caminho_arquivo = os.path.join("data", "input", arquivo_enviado.name)
    os.makedirs(os.path.dirname(caminho_arquivo), exist_ok=True)
    with open(caminho_arquivo, "wb") as f:
        f.write(arquivo_enviado.getbuffer())

    try:
        #detecta o formato automaticamente
        formato = detectar_formato(caminho_arquivo)
        st.write(f"Formato detectado: **{formato.upper()}**")

        #escolhe o converter certo
        if formato == "gcp":
            df_focus = converter_gcp(caminho_arquivo)
        elif formato == "aws":
            df_focus = converter_aws(caminho_arquivo)
        elif formato == "azure":
            df_focus = converter_azure(caminho_arquivo)

        st.success("Conversão concluída!")

        #mostra o resultado como tabela na própria página
        st.dataframe(df_focus)

        #exibe o gráfico de custos por serviço
        fig = grafico_custos_por_servico(df_focus)
        st.plotly_chart(fig, use_container_width=True)

        #permite baixar o CSV padronizado
        csv_bytes = df_focus.to_csv(index=False).encode("utf-8")
        st.download_button(
            "Baixar CSV padronizado",
            data=csv_bytes,
            file_name="focus_padronizado.csv",
            mime="text/csv",
        )

    except Exception as erro:
        st.error(f"Erro durante a conversão: {erro}")
