import pandas as pd
import plotly.express as px

#colunas de custo que podem virar metrica ("valor") nos graficos, em ordem de preferencia
COLUNAS_DE_CUSTO = ["BilledCost", "EffectiveCost", "ContractedCost", "ListCost"]

#colunas categoricas que fazem sentido como dimensao de agrupamento, em ordem de prioridade
COLUNAS_DIMENSAO = ["ProviderName", "ServiceName", "ChargeCategory", "ServiceCategory", "SubAccountId", "BillingAccountId"]

#limite de categorias exibidas por grafico -- acima disso, o restante vira uma barra "Outros"
MAX_CATEGORIAS = 10

#paleta fixa por coluna de custo -- garante que a mesma cor sempre representa a mesma
#metrica em todos os graficos, em vez da cor mudar dependendo de quais colunas existem
CORES_POR_CUSTO = {
    "BilledCost": "#3b82f6",
    "EffectiveCost": "#22d3ee",
    "ContractedCost": "#f59e0b",
    "ListCost": "#94a3b8",
}


def _aplicar_tema(fig):
    #aplica o tema escuro do Plotly e deixa o fundo transparente,
    #pra combinar com o fundo escuro do app (nativo, via .streamlit/config.toml)
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#cbd5e1"),
        legend=dict(orientation="h", y=-0.2),
        margin=dict(t=48, b=16, l=8, r=8),
    )
    fig.update_xaxes(gridcolor="#1e293b")
    fig.update_yaxes(gridcolor="#1e293b")
    return fig


def _custos_disponiveis(df_focus):
    return [c for c in COLUNAS_DE_CUSTO if c in df_focus.columns and df_focus[c].notna().any()]


def calcular_kpis(df_focus):
    #resumo geral do dataset -- usado nos cartoes de metrica no topo da pagina
    colunas_valor = _custos_disponiveis(df_focus)
    total_faturado = df_focus["BilledCost"].sum() if "BilledCost" in colunas_valor else None
    total_efetivo = df_focus["EffectiveCost"].sum() if "EffectiveCost" in colunas_valor else None

    economia = None
    economia_pct = None
    if total_faturado is not None and total_efetivo is not None and total_faturado != 0:
        economia = total_faturado - total_efetivo
        economia_pct = (economia / total_faturado) * 100

    servico_top = None
    if "ServiceName" in df_focus.columns and "BilledCost" in colunas_valor:
        por_servico = df_focus.groupby("ServiceName")["BilledCost"].sum()
        if not por_servico.empty:
            servico_top = por_servico.idxmax()

    return {
        "registros": len(df_focus),
        "total_faturado": total_faturado,
        "total_efetivo": total_efetivo,
        "economia": economia,
        "economia_pct": economia_pct,
        "servico_top": servico_top,
    }


def _agrupar_com_outros(df_focus, coluna_dimensao, colunas_valor):
    agrupado = df_focus.groupby(coluna_dimensao)[colunas_valor].sum().reset_index()
    agrupado = agrupado.sort_values(colunas_valor[0], ascending=False)

    if len(agrupado) <= MAX_CATEGORIAS:
        return agrupado

    principais = agrupado.iloc[:MAX_CATEGORIAS]
    resto = agrupado.iloc[MAX_CATEGORIAS:][colunas_valor].sum()
    linha_outros = pd.DataFrame([{coluna_dimensao: "Outros", **resto}])
    return pd.concat([principais, linha_outros], ignore_index=True)


def grafico_por_dimensao(df_focus, coluna_dimensao):
    colunas_valor = _custos_disponiveis(df_focus)
    if not colunas_valor or coluna_dimensao not in df_focus.columns:
        return None
    if not df_focus[coluna_dimensao].notna().any():
        return None

    agrupado = _agrupar_com_outros(df_focus, coluna_dimensao, colunas_valor)

    agrupado_melted = agrupado.melt(
        id_vars=coluna_dimensao,
        value_vars=colunas_valor,
        var_name="Tipo de Custo",
        value_name="Valor",
    )

    fig = px.bar(
        agrupado_melted,
        x=coluna_dimensao,
        y="Valor",
        color="Tipo de Custo",
        color_discrete_map=CORES_POR_CUSTO,
        barmode="group",
        title=f"Custos por {coluna_dimensao}",
    )
    fig.update_yaxes(tickprefix="$", tickformat=",.2f")
    return _aplicar_tema(fig)


def grafico_evolucao_temporal(df_focus, coluna_data="ChargePeriodStart"):
    colunas_valor = _custos_disponiveis(df_focus)
    if not colunas_valor or coluna_data not in df_focus.columns:
        return None

    datas = pd.to_datetime(df_focus[coluna_data], errors="coerce")
    if datas.notna().sum() < 2:
        return None

    df_tempo = df_focus.copy()
    df_tempo[coluna_data] = datas
    agrupado = df_tempo.groupby(coluna_data)[colunas_valor].sum().reset_index()

    agrupado_melted = agrupado.melt(
        id_vars=coluna_data,
        value_vars=colunas_valor,
        var_name="Tipo de Custo",
        value_name="Valor",
    )

    fig = px.area(
        agrupado_melted,
        x=coluna_data,
        y="Valor",
        color="Tipo de Custo",
        color_discrete_map=CORES_POR_CUSTO,
        title="Evolução de custos ao longo do tempo",
    )
    fig.update_traces(line=dict(width=2))
    fig.update_yaxes(tickprefix="$", tickformat=",.2f")
    return _aplicar_tema(fig)


def gerar_graficos(df_focus):
    graficos = []

    fig_tempo = grafico_evolucao_temporal(df_focus)
    if fig_tempo is not None:
        graficos.append(fig_tempo)

    for coluna in COLUNAS_DIMENSAO:
        if coluna == "ProviderName" and df_focus.get("ProviderName", pd.Series(dtype=object)).nunique() <= 1:
            continue
        fig = grafico_por_dimensao(df_focus, coluna)
        if fig is not None:
            graficos.append(fig)

    return graficos