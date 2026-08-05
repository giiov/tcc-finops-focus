import pandas as pd
import json

from src.mapping.azure_mapping import AZURE_MAPPING
from src.schemas.focus_schema import COLUNAS_OFICIAIS_FOCUS

def converter_azure():
    caminho_entrada = "data/input/custos_azure.csv"
    caminho_saida = "data/output/focus_padronizado_azure.csv"

    #leitura
    df = pd.read_csv(caminho_entrada)

    #renomeando colunas
    df = df.rename(columns=AZURE_MAPPING)

    #Ajusta os limites de data (Azure entrega datas com limite INCLUSIVO,
    #o FOCUS exige limite EXCLUSIVO em BillingPeriodEnd e ChargePeriodEnd)
    if "BillingPeriodEndDate" in df.columns:
        df["BillingPeriodEnd"] = pd.to_datetime(df["BillingPeriodEndDate"]) + pd.Timedelta(days=1)
    else:
        df["BillingPeriodEnd"] = None

    if "ChargePeriodStart" in df.columns:
        df["ChargePeriodEnd"] = pd.to_datetime(df["ChargePeriodStart"]) + pd.Timedelta(days=1)
    else:
        df["ChargePeriodEnd"] = None

    #Injeção de Provedor
    #diferente do GCP, o Azure não tem uma coluna própria pra isso -- é sempre "Microsoft"
    df["ProviderName"] = "Microsoft"

    #Trata o Invoice Issuer
    #normalmente vem em PartnerName, mas fica vazio quando não há parceiro/revenda envolvido
    if "PartnerName" in df.columns:
        df["InvoiceIssuerName"] = df["PartnerName"].fillna("Microsoft")
        df.loc[df["InvoiceIssuerName"] == "", "InvoiceIssuerName"] = "Microsoft"
    else:
        df["InvoiceIssuerName"] = "Microsoft"

    #Trata a categoria da cobrança
    #o Azure tem uma coluna "ChargeType" que diz se é uso, compra, reembolso etc.
    #aqui traduzimos os valores dela pros valores que o FOCUS espera
    MAPA_CHARGE_CATEGORY = {
        "Usage": "Usage",
        "Purchase": "Purchase",
        "Credit": "Credit",
        "Tax": "Tax",
        "UnusedReservation": "Usage",
        "UnusedSavingsPlan": "Usage",
        "Refund": "Purchase",
    }

    if "ChargeType" in df.columns:
        #map() vai trocar cada valor da coluna pelo valor equivalente no dicionário acima
        df["ChargeCategory"] = df["ChargeType"].map(MAPA_CHARGE_CATEGORY)

        #se aparecer algum valor de ChargeType que a gente não previu no dicionário, cobrimos com caso padrão
        df["ChargeCategory"] = df["ChargeCategory"].fillna("Adjustment")
    else:
        #se a fonte não tiver ChargeType, assume Usage pra tudo
        df["ChargeCategory"] = "Usage"

    #Trata a Classe da Cobrança (ChargeClass)
    #só existe um valor permitido no FOCUS aqui: "Correction", usado quando a linha
    #é um reembolso (Refund) referente a um período de fatura já encerrado
    if "ChargeType" in df.columns:
        df["ChargeClass"] = df["ChargeType"].apply(lambda tipo: "Correction" if tipo == "Refund" else None)
    else:
        df["ChargeClass"] = None

    #Trata o Custo Cobrado (BilledCost)
    #no Azure, "CostInBillingCurrency" é o custo já calculado, mas linhas de Usage
    #cobertas por uma reserva/savings plan (PricingModel) já foram pagas na compra --
    #então o valor faturado dessa linha específica de uso precisa ser zerado
    def calcular_billed_cost(linha):
        custo = linha.get("CostInBillingCurrency")
        tipo_cobranca = linha.get("ChargeType", "")
        modelo_precificacao = linha.get("PricingModel", "")

        if tipo_cobranca == "Usage" and modelo_precificacao in ("Reservation", "SavingsPlan"):
            return 0

        return custo

    if "CostInBillingCurrency" in df.columns:
        df["BilledCost"] = df.apply(calcular_billed_cost, axis=1)
    else:
        df["BilledCost"] = None

    #Trata o Custo Efetivo (EffectiveCost)
    #a conversão oficial da Microsoft usa um dataset amortizado separado pra essa coluna;
    #enquanto não temos acesso a esse segundo dataset, aproximamos EffectiveCost = BilledCost
    #(limitação a documentar no TCC, igual foi feito no GCP quando não havia coluna de créditos)
    if "EffectiveCost" not in df.columns:
        df["EffectiveCost"] = df["BilledCost"]

    #Trata o Custo Contratado (ContractedCost)
    #calculado como preço unitário vezes quantidade consumida
    if "UnitPrice" in df.columns and "Quantity" in df.columns:
        df["ContractedCost"] = df["UnitPrice"] * df["Quantity"]
    else:
        df["ContractedCost"] = df["BilledCost"]

    #Trata Categoria e Nome do Serviço (ServiceCategory / ServiceName)
    #o mapeamento oficial da Microsoft usa uma tabela de lookup própria
    #(ConsumedService + ResourceType -> ServiceCategory/ServiceName) que não
    #reproduzimos por completo aqui -- fica só uma versão simplificada,
    #cobrindo os serviços mais comuns, como limitação documentada no TCC
    MAPA_SERVICE_CATEGORY = {
        "Virtual Machines": "Compute",
        "Azure App Service": "Compute",
        "Storage": "Storage",
        "SQL Database": "Databases",
        "Azure Database for PostgreSQL": "Databases",
        "Virtual Network": "Networking",
        "Azure DNS": "Networking",
    }

    if "ConsumedService" in df.columns:
        df["ServiceCategory"] = df["ConsumedService"].map(MAPA_SERVICE_CATEGORY).fillna("Other")
        df["ServiceName"] = df["ConsumedService"]
    else:
        df["ServiceCategory"] = "Other"
        df["ServiceName"] = "Unknown"

    #Tags (Estrutura JSON padrão)
    #No Azure, Tags vem como texto "quase-JSON", ex: '"ambiente": "producao", "time": "financas"'
    #ou vazio quando o recurso não tem nenhuma tag -- falta só a chave/fecha-chave pra ser JSON válido
    def converter_tags_azure(tags_raw):
        #Caso não haja tags (célula vazia ou NaN)
        if pd.isna(tags_raw) or str(tags_raw).strip() == "":
            return json.dumps({})

        bruto = str(tags_raw).strip()

        #se já vier com as chaves (algumas contas/exports já trazem), não duplica
        if not bruto.startswith("{"):
            bruto = "{" + bruto + "}"

        try:
            dicionario_tags = json.loads(bruto)
        except json.JSONDecodeError:
            return json.dumps({})

        return json.dumps(dicionario_tags)

    if "Tags" in df.columns:
        df["Tags"] = df["Tags"].apply(converter_tags_azure)
    else:
        df["Tags"] = json.dumps({})

    #mantendo apenas as colunas oficiais do FOCUS
    #caso alguma coluna não exista, será criada sozinha
    for coluna in COLUNAS_OFICIAIS_FOCUS:
        if coluna not in df.columns:
            df[coluna] = None

    #organiza as colunas na ordem oficial do FOCUS
    df_focus = df[COLUNAS_OFICIAIS_FOCUS]

    #exporta o arquivo convertido
    df_focus.to_csv(caminho_saida, index=False)

    print("Conversão Azure -> FOCUS concluída com sucesso")

if __name__ == "__main__":
    converter_azure()