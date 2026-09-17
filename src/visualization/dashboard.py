import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

COLUNAS_DE_CUSTO = ["BilledCost", "EffectiveCost", "ContractedCost", "ListCost"]
COLUNAS_DIMENSAO = ["ProviderName", "ServiceName", "ChargeCategory", "ServiceCategory", "SubAccountId", "BillingAccountId"]
MAX_CATEGORIAS = 10
COLUNAS_IGNORADAS_SE_UNICAS = ["ProviderName", "BillingAccountId"]

CORES_POR_CUSTO = {
    "BilledCost":      "#FF33A1", # Rosa Vibrante
    "EffectiveCost":   "#00F2FE", # Ciano Brilhante
    "ContractedCost":  "#9D4EDD", # Roxo Eletrico
    "ListCost":        "#FFB142", # Laranja/Dourado
}

CORES_POR_CATEGORIA = [
    "#FF33A1",
    "#00F2FE",
    "#FFB142",
    "#9D4EDD",
    "#FF007F",
    "#00FFCC",
    "#FF7300",
    "#3366FF",
    "#CCFF00",
    "#B000FF",
]

def _aplicar_tema(fig):
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(255,255,255,0.02)",
        font=dict(family="Inter", color="#d0c9cd"),
        legend=dict(orientation="h", y=-0.15, font=dict(size=11)),
        margin=dict(t=65, b=20, l=20, r=20),
        title=dict(font=dict(size=15, color="#FFFFFF"), x=0.02, y=0.95)
    )
    fig.update_xaxes(gridcolor="#3a2850", zerolinecolor="#4d3b66")
    fig.update_yaxes(gridcolor="#3a2850", zerolinecolor="#4d3b66")
    return fig

def _custos_disponiveis(df_focus):
    return [c for c in COLUNAS_DE_CUSTO if c in df_focus.columns and df_focus[c].notna().any()]

def calcular_kpis(df_focus):
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

    if coluna_dimensao == "ChargeCategory":
        valores_waterfall = agrupado.copy()
        col_v = colunas_valor[0]
        fig = go.Figure(go.Waterfall(
            orientation="v",
            measure=["relative"] * len(valores_waterfall),
            x=valores_waterfall[coluna_dimensao],
            y=valores_waterfall[col_v],
            textposition="outside",
            text=[f"${v:,.0f}" for v in valores_waterfall[col_v]],
            decreasing={"marker": {"color": "#00F2FE"}}, # Ciano (Reducoes)
            increasing={"marker": {"color": "#FF33A1"}}, # Rosa (Custos)
            totals={"marker": {"color": "#9D4EDD"}} # Roxo Eletrico (Total)
        ))
        fig.update_layout(title=f"Custos por {coluna_dimensao}", waterfallgap=0.3)
        fig.update_yaxes(tickprefix="$", tickformat=",.2f")
        return _aplicar_tema(fig)

    if coluna_dimensao == "ServiceName":
        agrupado_melted = agrupado.melt(
            id_vars=coluna_dimensao, value_vars=colunas_valor,
            var_name="Tipo de Custo", value_name="Valor",
        )
        fig = px.bar(
            agrupado_melted, x="Valor", y=coluna_dimensao,
            color="Tipo de Custo", color_discrete_map=CORES_POR_CUSTO,
            barmode="group", orientation="h", title=f"Custos por {coluna_dimensao}",
        )
        fig.update_xaxes(tickprefix="$", tickformat=",.2f")
        fig.update_layout(xaxis_title="Valor", yaxis_title=coluna_dimensao, bargap=0.2, height=450)
        fig.update_yaxes(autorange="reversed")
        return _aplicar_tema(fig)

    if coluna_dimensao == "SubAccountId":
        categorias = agrupado[coluna_dimensao].astype(str).tolist()
        fig = go.Figure()
        for coluna_valor in colunas_valor:
            valores = agrupado[coluna_valor].tolist()
            x_linhas = []
            y_linhas = []
            for categoria, valor in zip(categorias, valores):
                x_linhas.extend([0, valor, None])
                y_linhas.extend([categoria, categoria, None])

            cor = CORES_POR_CUSTO[coluna_valor]
            fig.add_trace(go.Scatter(
                x=x_linhas, y=y_linhas, mode="lines",
                line=dict(color=cor, width=2), name=coluna_valor,
                legendgroup=coluna_valor, hoverinfo="skip", showlegend=False,
            ))
            fig.add_trace(go.Scatter(
                x=valores, y=categorias, mode="markers",
                marker=dict(color=cor, size=10), name=coluna_valor,
                legendgroup=coluna_valor, customdata=valores,
                hovertemplate=f"{coluna_dimensao}: %{{y}}<br>{coluna_valor}: $%{{x:,.2f}}<extra></extra>",
            ))
        fig.update_layout(title=f"Custos por {coluna_dimensao}", xaxis_title="Valor", yaxis_title=coluna_dimensao, height=450)
        fig.update_yaxes(type="category")
        fig.update_xaxes(tickprefix="$", tickformat=",.2f", rangemode="tozero")
        fig.update_yaxes(autorange="reversed")
        return _aplicar_tema(fig)

    if coluna_dimensao == "BillingAccountId":
        if len(colunas_valor) >= 2:
            eixo_x = colunas_valor[0]
            eixo_y = colunas_valor[1]
            fig = px.scatter(
                agrupado, x=eixo_x, y=eixo_y, text=coluna_dimensao,
                color_discrete_sequence=["#FF33A1"], title=f"Custos por {coluna_dimensao}",
            )
            fig.update_traces(marker=dict(size=12, line=dict(width=1.5, color="#00F2FE")), textposition="top center", textfont=dict(size=9))
            fig.update_xaxes(tickprefix="$", tickformat=",.2f", title=eixo_x)
            fig.update_yaxes(tickprefix="$", tickformat=",.2f", title=eixo_y)
        else:
            col_valor = colunas_valor[0]
            fig = px.scatter(
                agrupado, x=coluna_dimensao, y=col_valor, size=col_valor,
                text=coluna_dimensao, color_discrete_sequence=["#FF33A1"], title=f"Custos por {coluna_dimensao}",
            )
            fig.update_traces(marker=dict(line=dict(width=1.5, color="#00F2FE")), textposition="top center", textfont=dict(size=9))
            fig.update_yaxes(tickprefix="$", tickformat=",.2f")
        return _aplicar_tema(fig)

    agrupado_melted = agrupado.melt(
        id_vars=coluna_dimensao, value_vars=colunas_valor,
        var_name="Tipo de Custo", value_name="Valor",
    )
    fig = px.bar(
        agrupado_melted, x=coluna_dimensao, y="Valor", color="Tipo de Custo",
        color_discrete_map=CORES_POR_CUSTO, barmode="group", title=f"Custos por {coluna_dimensao}",
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
        id_vars=coluna_data, value_vars=colunas_valor,
        var_name="Tipo de Custo", value_name="Valor",
    )
    fig = px.area(
        agrupado_melted, x=coluna_data, y="Valor", color="Tipo de Custo",
        color_discrete_map=CORES_POR_CUSTO, title="Evolução de custos ao longo do tempo",
    )
    fig.update_traces(line=dict(width=2))
    fig.update_yaxes(tickprefix="$", tickformat=",.2f")
    fig.update_layout(height=350)
    return _aplicar_tema(fig)

def gerar_graficos(df_focus):
    graficos = {}
    fig_tempo = grafico_evolucao_temporal(df_focus)
    if fig_tempo is not None:
        graficos['tempo'] = fig_tempo

    for coluna in COLUNAS_DIMENSAO:
        if coluna in COLUNAS_IGNORADAS_SE_UNICAS and df_focus.get(coluna, pd.Series(dtype=object)).nunique() <= 1:
            continue
        fig = grafico_por_dimensao(df_focus, coluna)
        if fig is not None:
            graficos[coluna] = fig

    return graficos