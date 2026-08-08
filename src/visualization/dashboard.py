import plotly.express as px

#gera um gráfico de barras comparando custo faturado x custo efetivo, por serviço
#é apenas a base do dashboard - outras visualizações (ex: distribuição por Tags) podem ser adicionadas aq como novas funções
#seguindo esse mesmo padrão:
#receber o df_focus já padronizado, devolvem uma figura do Plotly pronta

def grafico_custos_por_servico(df_focus):
    df_srv = df_focus.groupby("ServiceName")[["BilledCost", "EffectiveCost"]].sum().reset_index()

    df_srv_melted = df_srv.melt(
        id_vars="ServiceName",
        value_vars=["BilledCost","EffectiveCost"],
        var_name="Tipo de Custo",
        value_name="Valor ($)",
    )

    fig = px.bar(
        df_srv_melted,
        x="ServiceName",
        y="Valor ($)",
        color="Tipo de Custo",
        barmode="group",
        title="Custos por Serviço (Faturado vs Efetivo)",

    )

    return fig