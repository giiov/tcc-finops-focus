import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns


from src.mapping.aws_mapping import AWS_MAPPING
from src.schemas.focus_schema import COLUNAS_OFICIAIS_FOCUS

def converter_aws():
    caminho_entrada = "data/input/custos_aws.csv"
    caminho_saida = "data/output/focus_padronizado_aws.csv"

    #leitura 
    df = pd.read_csv(caminho_entrada)

    #renomeando colunas
    df = df.rename(columns=AWS_MAPPING)

    #criando tabelas que não existem no CUR
    df["ProviderName"] = "AWS"
    df["PublisherName"] = "AWS"

    #manter apenas colunas focus
    df_focus = df[COLUNAS_OFICIAIS_FOCUS]

    #exportar
    df_focus.to_csv(caminho_saida, index=False)

    print("Gráfico FOCUS gerado com sucesso")

    #GRÁFICO!!
    # cria uma janela dividida em duas partes
    fig, axes = plt.subplots(1, 2, figsize=(15, 6))
    fig.suptitle('Dashboard Executivo FinOps - Modelo FOCUS', fontsize=16, fontweight='bold', color='#0f172a')
    
    #gráfico esquerdo: comparativo de custos por serviço (Billed vs Effective)
    df_srv = df.groupby('ServiceName')[['BilledCost', 'EffectiveCost']].sum().reset_index()
    df_srv_melted = df_srv.melt(id_vars='ServiceName', value_vars=['BilledCost', 'EffectiveCost'], 
                                var_name='Tipo de Custo', value_name='Valor ($)')
    
    sns.barplot(data=df_srv_melted, x='Valor ($)', y='ServiceName', hue='Tipo de Custo', ax=axes[0], palette=['#2563eb', '#10b981'])
    axes[0].set_title('Custos por Serviço (Faturado vs Efetivo)', fontsize=12, fontweight='bold')
    axes[0].set_ylabel('')
    
    #gráfico direito: distribuição percentual do gasto por Tag/Ambiente (Pizza)
    if 'Tags' in df.columns and not df['Tags'].isnull().all():
        df_tag = df.groupby('Tags')['BilledCost'].sum().reset_index()
        axes[1].pie(df_tag['BilledCost'], labels=df_tag['Tags'], autopct='%1.1f%%', 
                    colors=['#6366f1', '#f59e0b', '#ec4899'], startangle=140,
                    textprops={'fontsize': 10, 'weight': 'bold'})
        axes[1].set_title('Distribuição de Custos por Ambiente (Tags)', fontsize=12, fontweight='bold')
    
    #ajuste de espaçamento na tela
    plt.tight_layout()
    
    #salva uma cópia em imagem
    caminho_grafico = 'data/output/dashboard_focus_completo.png'
    plt.savefig(caminho_grafico, dpi=150)
    print(f" Imagem do dashboard salva em: {caminho_grafico}")
    
    #mostra na tela automaticamente
    print("Exibindo visualização...")
    plt.show()

if __name__ == "__main__":
    converter_aws()