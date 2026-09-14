import pandas as pd
import json

from src.mapping.oracle_mapping import ORACLE_MAPPING
from src.schemas.focus_schema import COLUNAS_OFICIAIS_FOCUS

def converter_oracle(caminho_arquivo):
    # ALTERAÇÃO: Atualizado para receber 'caminho_arquivo' como parâmetro, seguindo o padrão AWS/GCP/Azure
    #leitura
    df = pd.read_csv(caminho_arquivo)

    #renomeando colunas
    df = df.rename(columns=ORACLE_MAPPING)

    #Injeção de Provedor, Publicador e Emissor da Fatura
    #a própria documentação da Oracle trata esses três como constantes fixas
    #(não existe coluna de origem pra nenhum dos três no cost report proprietário)
    df["ProviderName"] = "Oracle"
    df["PublisherName"] = "Oracle"
    df["InvoiceIssuerName"] = "Oracle"

    #Trata o Nome da Conta de Cobrança (BillingAccountName)
    #a Oracle documenta esse campo como nulo até no próprio export FOCUS oficial dela --
    #ou seja, essa não é uma limitação nossa, é uma limitação do provedor
    df["BillingAccountName"] = None

    #Trata o Período de Cobrança (BillingPeriodStart/End)
    #a OCI não expõe essas datas diretamente; aproximamos pelo mês-calendário
    #do ChargePeriodStart (limitação documentada -- o ciclo de fatura real pode
    #ser diferente do mês-calendário, a própria Oracle avisa isso na doc oficial)
    if "ChargePeriodStart" in df.columns:
        datas_uso = pd.to_datetime(df["ChargePeriodStart"])
        df["BillingPeriodStart"] = datas_uso.values.astype("datetime64[M]")
        df["BillingPeriodEnd"] = df["BillingPeriodStart"] + pd.offsets.MonthBegin(1)
    else:
        df["BillingPeriodStart"] = None
        df["BillingPeriodEnd"] = None

    #Trata a Categoria e a Classe da Cobrança (ChargeCategory / ChargeClass)
    #a Oracle amarra os dois conceitos à mesma coluna de origem: lineItem/isCorrection
    #(True = a linha é uma correção de uma cobrança anterior)
    if "lineItem/isCorrection" in df.columns:
        eh_correcao = df["lineItem/isCorrection"].astype(str).str.strip().str.upper() == "TRUE"
        df["ChargeCategory"] = eh_correcao.map({True: "Adjustment", False: "Usage"})
        df["ChargeClass"] = eh_correcao.map({True: "Correction", False: None})
    else:
        df["ChargeCategory"] = "Usage"
        df["ChargeClass"] = None

    #Trata o Custo Efetivo (EffectiveCost)
    #diferente do Azure, aqui não é uma aproximação: a própria Oracle usa a mesma
    #coluna de origem (cost/myCost) tanto pra BilledCost quanto pra EffectiveCost
    df["EffectiveCost"] = df["BilledCost"]

    #Trata Custo Contratado e Custo de Lista (ContractedCost / ListCost)
    #nenhum dos dois tem coluna de origem nem no export oficial da Oracle --
    #aproximamos pelo BilledCost, como limitação documentada (mesma que a própria Oracle tem)
    df["ContractedCost"] = df["BilledCost"]
    df["ListCost"] = df["BilledCost"]

    #Trata a Categoria do Serviço (ServiceCategory)
    #a OCI não fornece essa taxonomia -- precisa de uma tabela de tradução própria
    #a partir do nome do serviço (product/service), igual fizemos no Azure
    MAPA_SERVICE_CATEGORY = {
        "Compute": "Compute",
        "Object Storage": "Storage",
        "Block Storage": "Storage",
        "Database": "Databases",
        "Autonomous Database": "Databases",
        "Networking": "Networking",
        "Virtual Cloud Network": "Networking",
    }

    if "ServiceName" in df.columns:
        df["ServiceCategory"] = df["ServiceName"].map(MAPA_SERVICE_CATEGORY).fillna("Other")
    else:
        df["ServiceCategory"] = "Other"

    #Trata o Tipo de Recurso (ResourceType)
    #limitação do provedor, não nossa: a documentação oficial da Oracle afirma
    #explicitamente que esse valor não é publicado em nenhum cost report
    df["ResourceType"] = None

    #Tags (consolidação dinâmica de colunas)
    #Na Oracle, cada tag vira uma coluna própria, prefixada com "tags/"
    #(ex.: "tags/Oracle-Tags.CreatedBy") -- mesma lógica de consolidação dinâmica
    #já usada no aws_converter.py pro prefixo "resourceTags/user:", só troca o prefixo
    colunas_de_tags = [coluna for coluna in df.columns if coluna.startswith("tags/")]

    def montar_tags(linha):
        dicionario_tags = {}
        for coluna in colunas_de_tags:
            valor = linha[coluna]
            if pd.notna(valor) and str(valor).strip() != "":
                #remove o prefixo "tags/" pra ficar só o nome da tag
                chave = coluna.replace("tags/", "", 1)
                dicionario_tags[chave] = valor
        return json.dumps(dicionario_tags)

    if colunas_de_tags:
        df["Tags"] = df.apply(montar_tags, axis=1)
    else:
        df["Tags"] = json.dumps({})

    #mantendo apenas as colunas oficiais do FOCUS
    #caso alguma coluna não exista, será criada sozinha
    for coluna in COLUNAS_OFICIAIS_FOCUS:
        if coluna not in df.columns:
            df[coluna] = None

    #organiza as colunas na ordem oficial do FOCUS
    df_focus = df[COLUNAS_OFICIAIS_FOCUS]

    # ALTERAÇÃO: Atualizado para retornar o DataFrame em vez de salvar diretamente no disco
    #devolve o df padronizado
    return df_focus

if __name__ == "__main__":
    # teste rápido e isolado deste converter
    resultado = converter_oracle("data/input/custos_oracle.csv")
    print(resultado.head())