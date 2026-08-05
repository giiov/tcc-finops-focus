import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import json


from src.mapping.aws_mapping import AWS_MAPPING
from src.schemas.focus_schema import COLUNAS_OFICIAIS_FOCUS

def converter_aws():
    caminho_entrada = "data/input/custos_aws.csv"
    caminho_saida = "data/output/focus_padronizado"

    #leitura 
    df = pd.read_csv(caminho_entrada)

    #Tratamento dinâmico do ResourceType
    if "product/instanceType" in df.columns and "product/productFamily" in df.columns:
        df["ResourceType"] = df["product/instanceType"].fillna(df["product/productFamily"])
    elif "product/instanceType" in df.columns:
        df["ResourceType"] = df["product/instanceType"].fillna(df.get("lineItem/ProductCode", "General"))
    elif "product/productFamily" in df.columns:
        df["ResourceType"] = df["product/productFamily"]
    else:
        df["ResourceType"] = "General"

    #renomeando colunas
    df = df.rename(columns=AWS_MAPPING)

    #tratando categoria de cobrança
    #o CUR AWS tem uma coluna "lineItem/LineItemType" com vários valores possíveis 
    #vamos traduzir cada um pro valor equivalente que o FOCUS espera
    MAPA_CHARGE_CATEGORY = {
        "Usage": "Usage",
        "DiscountedUsage": "Usage",
        "SavingsPlanCoveredUsage": "Usage",
        "Tax": "Tax",
        "Fee": "Purchase",
        "RIFee": "Purchase",
        "SavingsPlanUpfrontFee": "Purchase",
        "SavingsPlanRecurringFee": "Purchase",
        "Credit": "Credit",
        "Refund": "Credit",
        "Discount": "Adjustment",
        "SavingsPlanNegation": "Adjustment",
    }

    if "lineItem/LineItemType" in df.columns:
        df["ChargeCategory"] = df["lineItem/LineItemType"].map(MAPA_CHARGE_CATEGORY)
        df["ChargeCategory"] = df["ChargeCategory"].fillna("Usage")
    else:
        df["ChargeCategory"] = "Usage"
        
    #criando tabelas que não existem no CUR
    df["ProviderName"] = "AWS"

    # Garante que se o PublisherName estiver vazio/NaN, assume "Amazon Web Services"
    if "PublisherName" in df.columns:
        df["PublisherName"] = df["PublisherName"].fillna("Amazon Web Services")
    else:
        df["PublisherName"] = "Amazon Web Services"

    #Tags (Estrutura JSON padrão)
    #No AWS CUR, cada tag vira uma coluna própria
    #Ex: resourceTags/user:Environment, resourceTags/user:Team
    colunas_de_tags = [coluna for coluna in df.columns if coluna.startswith("resourceTags/")]

    def converter_linha_para_tags(linha):
        dicionario_tags = {}
        for coluna in colunas_de_tags:
            valor = linha[coluna]
            if pd.notna(valor) and str(valor).strip() != "":
                nome_tag = coluna.split(":", 1)[1] if ":" in coluna else coluna
                dicionario_tags[nome_tag] = valor
        return json.dumps(dicionario_tags)

    if colunas_de_tags:
        df["Tags"] = df.apply(converter_linha_para_tags, axis=1)
    else:
        df["Tags"] = json.dumps({})
        
    #no AWS CUR, cada tag vira uma coluna própria
    #ex: resourceTags/user:Environment, resourceTags/user:Team
    colunas_de_tags = [coluna for coluna in df.columns if coluna.startswith("resourceTags/")]

    def converter_linha_para_tags(linha):
        dicionario_tags = {}
        for coluna in colunas_de_tags:
            valor = linha[coluna]
            #só inclui a tag se o valor não for vazio/NaN naquela linha
            if pd.notna(valor) and str(valor).strip() != "":
                #remove o prefixo "resourceTags/user:" ou "resourceTags/aws:", mantendo só o nome da tag
                nome_tag = coluna.split(":", 1)[1] if ":" in coluna else coluna
                dicionario_tags[nome_tag] = valor
        return json.dumps(dicionario_tags)

    if colunas_de_tags:
        df["Tags"] = df.apply(converter_linha_para_tags, axis=1)
    else:
        df["Tags"] = json.dumps({})

    #garante que todas as colunas obrigatórias do focus existam
    #mesmo que a fonte não tenha esse dado, fica como vazio/none
    for coluna in COLUNAS_OFICIAIS_FOCUS:
        if coluna not in df.columns:
            df[coluna] = None

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