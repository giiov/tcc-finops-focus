import pandas as pd
import json

from src.mapping.gcp_mapping import GCP_MAPPING
from src.schemas.focus_schema import COLUNAS_OFICIAIS_FOCUS

def converter_gcp(caminho_arquivo):
    #leitura
    df = pd.read_csv(caminho_arquivo)
    
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
    #o GCP tem uma coluna "cost_type" que diz se a cobrança é normal, imposto ou ajuste
    #aqui traduzimos os valores dela prpos valores que o FOCUS espera
    MAPA_CHARGE_CATEGORY = {
        "regular": "Usage",
        "tax": "Tax",
        "adjustment": "Adjustment",
        "rouding_error": "Adjustment",
    }

    if "cost_type" in df.columns:
        #map() vai trocar cada valor da coluna pelo valor equivalente no dicionário acima
        df["ChargeCategory"] = df["cost_type"].map(MAPA_CHARGE_CATEGORY)

        #se aparecer algum valor de cost_type que a gente não previu no dicionário, cobrimos com caso padrão
        df["ChargeCategory"] = df["ChargeCategory"].fillna("Usage")

    else:
        #se a fonte não tiver cosy_type, assume Usage pra tudo
        df["ChargeCategory"] = "Usage"

    #trata o Custo CObrado (BilledCOst), aplicando os créditos/descontos
    # #no GCP, "cost" é o valor de tabela (sem desconto) e "credits" é uma lista de descontos aplicados 
    # vai chegar como texto (JSON) dentro de uma célula do CSV    
    def calcular_billed_cost(linha):
        custo_base = linha["cost"]
        texto_creditos = linha.get("credits", "[]")

        #se a linha não tiver créditos (célula vazia ou "[]") o custo base já é o final
        if pd.isna(texto_creditos) or texto_creditos in ("", "[]"):
            return custo_base

        #transforma o texto "[{...}, {...}]" em uma lista de dicionário python de verdade    
        lista_creditos = json.loads(texto_creditos)

        #soma o valor de cada crédito (já vem negativo no GCP, então somar já desconta)
        soma_dos_creditos = sum(credito["amount"] for credito in lista_creditos)

        return custo_base + soma_dos_creditos

    if "cost" in df.columns:
        df["BilledCost"] = df.apply(calcular_billed_cost, axis =1)
    else:
        df["BilledCost"] = None
    #Trata Custo Efetivo (Se não houver coluna de créditos mapeada por enquanto)
    if "EffectiveCost" not in df.columns:
        df["EffectiveCost"] = df["BilledCost"]

    #Tags (Estrutura JSON padrão)
    # No GCP, labels vêm como texto JSON, ex: '[{"key": "environment", "value": "production"}]'
    # ou "[]" quando o recurso não tem nenhuma label
    def converter_labels_para_tags(labels_raw):
        # Caso não haja labels (célula vazia, NaN ou "[]")
        if pd.isna(labels_raw) or str(labels_raw).strip() in ("", "[]"):
            return json.dumps({})

        try:
            lista_labels = json.loads(labels_raw)
        except (json.JSONDecodeError, TypeError):
            return json.dumps({})

        #monta o dicionário {key: value} a partir da lista de labels do GCP
        dicionario_tags = {
            item["key"]: item["value"]
            for item in lista_labels
            if isinstance(item, dict) and "key" in item and "value" in item
        }
        return json.dumps(dicionario_tags)

    if "labels" in df.columns:
        df["Tags"] = df["labels"].apply(converter_labels_para_tags)
    else:
        df["Tags"] = json.dumps({})

    #mantendo apenas as colunas oficiais do FOCUS
    #caso alguma coluna não exista, será criada sozinha
    for coluna in COLUNAS_OFICIAIS_FOCUS:
        if coluna not in df.columns:
            df[coluna] = None

    #organiza as colunas na ordem oficial do FOCUS
    df_focus = df[COLUNAS_OFICIAIS_FOCUS]

    #devolve o dataframe jpa padronizado
    return df_focus

if __name__ == "__main__":
    resultado = converter_gcp("data/input/custos_gcp.csv")
    print (resultado.head())