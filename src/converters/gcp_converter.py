import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

from src.mapping.gcp_mapping import GCP_MAPPING
from src.schemas.focus_schema import COLUNAS_OFICIAIS_FOCUS

def converter_gcp():
    caminho_entrada = "data/input/custos_gcp.csv"
    caminho_saida = "data/output/focus_padronizado"

    #leitura 
    df = pd.read_csv(caminho_entrada)
    
        #renomeando colunas
    df = df.rename(columns=GCP_MAPPING)

    #Tratamento dinâmico do ResourceId (Lida com relatórios Standard vs Detailed)
    if "resource.id" in df.columns:
        df["ResourceId"] = df["resource.id"].fillna(df["ChargeDescription"])
    elif "resource_id" in df.columns:
        df["ResourceId"] = df["resource_id"].fillna(df["ChargeDescription"])
    else:
        # Fallback caso a exportação seja do tipo Standard (sem IDs de recursos)
        df["ResourceId"] = df.get("ChargeDescription", df.get("ServiceName", "Unknown"))

        # 4. Tratamento do ResourceType
    if "ResourceType" not in df.columns:
        df["ResourceType"] = df["ServiceName"].fillna("General")

    #Injeção de Provedor e Publicador
    df["ProviderName"] = "GCP"
    df["PublisherName"] = "Google Cloud"

    #Trata a categoria da cobrança
    df["ChargeCategory"] = "Usage"

    #Trata Custo Efetivo (Se não houver coluna de créditos mapeada por enquanto)
    if "EffectiveCost" not in df.columns:
        df["EffectiveCost"] = df["BilledCost"]

    # 4. Tags (Estrutura JSON padrão)
    df["Tags"] = '{"Environment": "Untagged"}'