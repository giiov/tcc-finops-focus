import pandas as pd


from src.mapping.aws_mapping import AWS_MAPPING
from src.schemas.focus_schema import COLUNAS_OFICIAIS_FOCUS

def converter_aws(caminho_arquivo):
    #leitura
    df = pd.read_csv(caminho_arquivo)

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

    #garante que todas as colunas obrigatórias do focus existam
    #mesmo que a fonte não tenha esse dado, fica como vazio/none
    for coluna in COLUNAS_OFICIAIS_FOCUS:
        if coluna not in df.columns:
            df[coluna] = None

    #manter apenas colunas focus
    df_focus = df[COLUNAS_OFICIAIS_FOCUS]

    #devolve o df padronizado
    return df_focus

if __name__ == "__main__":
    #teste rápido e isolado deste converter, sem depender do main.py
    resultado = converter_aws("data/input/custos_aws.csv")
    print(resultado.head())