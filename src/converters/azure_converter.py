import json
import pandas as pd

from src.mapping.azure_mapping import AZURE_MAPPING
from src.schemas.focus_schema import COLUNAS_OFICIAIS_FOCUS


def converter_azure(caminho_arquivo):
    """
    Converte Azure Cost Management Cost Details
    para o subconjunto utilizado pelo projeto,
    baseado no FOCUS v1.4.

    O conversor evita inferências quando a fonte Azure
    não fornece informação suficiente para determinar
    semanticamente um atributo FOCUS.
    """

    # ============================================================
    # 1. LEITURA
    # ============================================================

    df = pd.read_csv(caminho_arquivo)


    # ============================================================
    # 2. COMPATIBILIDADE ENTRE VERSÕES DO COST DETAILS
    # ============================================================

    # Alguns exports utilizam BillingCurrencyCode
    # em vez de BillingCurrency.
    if (
        "BillingCurrency" not in df.columns
        and "BillingCurrencyCode" in df.columns
    ):
        df["BillingCurrency"] = df["BillingCurrencyCode"]


    # Alguns exports utilizam PreTaxCost
    # em vez de CostInBillingCurrency.
    if (
        "CostInBillingCurrency" not in df.columns
        and "PreTaxCost" in df.columns
    ):
        df["CostInBillingCurrency"] = df["PreTaxCost"]


    # Alguns exports utilizam ResourceRate
    # em vez de UnitPrice.
    if (
        "UnitPrice" not in df.columns
        and "ResourceRate" in df.columns
    ):
        df["UnitPrice"] = df["ResourceRate"]


    # Alguns exports utilizam UsageQuantity
    # em vez de Quantity.
    if (
        "Quantity" not in df.columns
        and "UsageQuantity" in df.columns
    ):
        df["Quantity"] = df["UsageQuantity"]


    # ============================================================
    # 3. MAPEAMENTOS DIRETOS
    # ============================================================

    df = df.rename(columns=AZURE_MAPPING)


    # ============================================================
    # 4. PROVEDOR
    # ============================================================

    df["ServiceProviderName"] = "Microsoft"
    df["HostProviderName"] = "Microsoft"


    # ============================================================
    # 5. INVOICE ISSUER
    # ============================================================

    # Para custos Azure diretos tratados pelo projeto.
    #
    # PartnerName não é utilizado automaticamente,
    # pois parceiro/publicador e emissor da fatura
    # não representam necessariamente o mesmo conceito.

    df["InvoiceIssuerName"] = "Microsoft"


    # ============================================================
    # 6. BILLING PERIOD
    # ============================================================

    if "BillingPeriodStart" in df.columns:

        df["BillingPeriodStart"] = pd.to_datetime(
            df["BillingPeriodStart"],
            errors="coerce",
            utc=True
        )

    else:

        df["BillingPeriodStart"] = None


    if "BillingPeriodEndDate" in df.columns:

        billing_end = pd.to_datetime(
            df["BillingPeriodEndDate"],
            errors="coerce",
            utc=True
        )

        # O fim recebido pelo Cost Details é tratado
        # como inclusivo.
        #
        # O schema do projeto utiliza limite exclusivo.
        df["BillingPeriodEnd"] = (
            billing_end
            + pd.Timedelta(days=1)
        )

    else:

        df["BillingPeriodEnd"] = None


    # ============================================================
    # 7. CHARGE PERIOD
    # ============================================================

    if "ChargePeriodStart" in df.columns:

        df["ChargePeriodStart"] = pd.to_datetime(
            df["ChargePeriodStart"],
            errors="coerce",
            utc=True
        )

        # A fonte utilizada possui granularidade diária.
        df["ChargePeriodEnd"] = (
            df["ChargePeriodStart"]
            + pd.Timedelta(days=1)
        )

    else:

        df["ChargePeriodStart"] = None
        df["ChargePeriodEnd"] = None


    # ============================================================
    # 8. CHARGE CATEGORY
    # ============================================================

    MAPA_CHARGE_CATEGORY = {
        "usage": "Usage",
        "purchase": "Purchase",
        "credit": "Credit",
        "tax": "Tax",
        "adjustment": "Adjustment",
    }


    if "ChargeType" in df.columns:

        charge_type = (
            df["ChargeType"]
            .astype("string")
            .str.strip()
            .str.lower()
        )

        df["ChargeCategory"] = (
            charge_type.map(
                MAPA_CHARGE_CATEGORY
            )
        )

    else:

        df["ChargeCategory"] = None


    # IMPORTANTE:
    #
    # Refund não é automaticamente classificado.
    #
    # Um Refund pode estar relacionado a Usage,
    # Purchase, Tax etc.
    #
    # Apenas ChargeType = Refund não fornece
    # informação suficiente para determinar
    # seguramente a ChargeCategory correspondente.


    # ============================================================
    # 9. CHARGE CLASS
    # ============================================================

    # Correction só deve ser utilizado quando sabemos
    # que a cobrança corrige um período de faturamento
    # previamente fechado.
    #
    # ChargeType sozinho não comprova essa condição.

    df["ChargeClass"] = None


    # ============================================================
    # 10. BILLED COST
    # ============================================================

    def calcular_billed_cost(linha):

        custo = pd.to_numeric(
            linha.get(
                "CostInBillingCurrency"
            ),
            errors="coerce"
        )

        if pd.isna(custo):
            return None

        tipo = str(
            linha.get(
                "ChargeType",
                ""
            )
        ).strip().lower()

        pricing_model = str(
            linha.get(
                "PricingModel",
                ""
            )
        ).strip().lower()

        eh_compromisso = (
            pricing_model
            in (
                "reservation",
                "savingsplan",
                "savings plan"
            )
        )

        # Uso coberto por compromisso não representa
        # uma nova cobrança nessa linha.
        if (
            tipo == "usage"
            and eh_compromisso
        ):
            return 0.0

        return custo


    if "CostInBillingCurrency" in df.columns:

        df["BilledCost"] = df.apply(
            calcular_billed_cost,
            axis=1
        )

    else:

        df["BilledCost"] = None


    # ============================================================
    # 11. EFFECTIVE COST
    # ============================================================

    def calcular_effective_cost(linha):

        billed_cost = pd.to_numeric(
            linha.get("BilledCost"),
            errors="coerce"
        )

        if pd.isna(billed_cost):
            return None

        tipo = str(
            linha.get(
                "ChargeType",
                ""
            )
        ).strip().lower()

        pricing_model = str(
            linha.get(
                "PricingModel",
                ""
            )
        ).strip().lower()

        eh_compromisso = (
            pricing_model
            in (
                "reservation",
                "savingsplan",
                "savings plan"
            )
        )


        # --------------------------------------------------------
        # Purchase de Reservation/Savings Plan
        # --------------------------------------------------------
        #
        # A cobrança existe em BilledCost.
        #
        # Entretanto, o EffectiveCost do compromisso
        # deve ser reconhecido no uso ao qual ele é
        # posteriormente alocado.
        #
        # Por isso:
        #
        # BilledCost    = valor da compra
        # EffectiveCost = 0

        if (
            tipo == "purchase"
            and eh_compromisso
        ):
            return 0.0


        # --------------------------------------------------------
        # Usage coberto por Reservation/Savings Plan
        # --------------------------------------------------------
        #
        # O Azure Actual Cost utilizado como fonte pelo
        # projeto não contém sozinho a parcela amortizada
        # necessária para reconstruir o EffectiveCost.
        #
        # BilledCost já será 0.
        #
        # Portanto, preservamos o valor disponível.
        #
        # Essa é uma limitação conhecida da fonte.
        #
        # Para reconstrução amortizada completa seria
        # necessário utilizar também Azure Amortized Cost.

        if (
            tipo == "usage"
            and eh_compromisso
        ):
            return billed_cost


        # --------------------------------------------------------
        # Demais cobranças
        # --------------------------------------------------------

        return billed_cost


    df["EffectiveCost"] = df.apply(
        calcular_effective_cost,
        axis=1
    )


    # ============================================================
    # 12. PRICING QUANTITY
    # ============================================================

    if "PricingQuantity" in df.columns:

        df["PricingQuantity"] = pd.to_numeric(
            df["PricingQuantity"],
            errors="coerce"
        )

    else:

        df["PricingQuantity"] = None


    # ============================================================
    # 13. PRICING UNIT
    # ============================================================

    if "PricingUnit" not in df.columns:
        df["PricingUnit"] = None


    # ============================================================
    # 14. REGRAS DE PRICING PARA TAX
    # ============================================================

    # Tax não representa uma quantidade de pricing
    # de um recurso/serviço.
    #
    # Portanto, PricingQuantity e PricingUnit
    # são removidos dessas linhas.

    mascara_tax = (
        df["ChargeCategory"] == "Tax"
    )

    df.loc[
        mascara_tax,
        "PricingQuantity"
    ] = None

    df.loc[
        mascara_tax,
        "PricingUnit"
    ] = None


    # ============================================================
    # 15. CONTRACTED COST
    # ============================================================

    # Para linhas em que UnitPrice e PricingQuantity
    # estão disponíveis:
    #
    # ContractedCost =
    # UnitPrice × PricingQuantity

    if (
        "UnitPrice" in df.columns
        and "PricingQuantity" in df.columns
    ):

        unit_price = pd.to_numeric(
            df["UnitPrice"],
            errors="coerce"
        )

        df["ContractedCost"] = (
            unit_price
            * df["PricingQuantity"]
        )

        # Quando o cálculo não puder ser realizado,
        # usamos o custo disponível como fallback
        # operacional do projeto.
        df["ContractedCost"] = (
            df["ContractedCost"]
            .fillna(df["BilledCost"])
        )

    else:

        df["ContractedCost"] = (
            df["BilledCost"]
        )


    # ============================================================
    # 16. LIST COST
    # ============================================================

    # Quando PaygCostInBillingCurrency está disponível,
    # ele foi mapeado para ListCost.
    #
    # Isso representa o custo calculado utilizando
    # preço Pay-As-You-Go/lista disponível na fonte.

    if "ListCost" in df.columns:

        df["ListCost"] = pd.to_numeric(
            df["ListCost"],
            errors="coerce"
        )

        df["ListCost"] = (
            df["ListCost"]
            .fillna(
                df["ContractedCost"]
            )
        )

    else:

        # Fallback operacional quando a fonte não
        # fornece explicitamente o custo de lista.
        df["ListCost"] = (
            df["ContractedCost"]
        )


    # ============================================================
    # 17. SERVICE NAME
    # ============================================================

    if "ServiceName" not in df.columns:
        df["ServiceName"] = None


    # ============================================================
    # 18. SERVICE CATEGORY
    # ============================================================

    # Classificação utilizando as categorias
    # do FOCUS adotadas pelo projeto.

    MAPA_SERVICE_CATEGORY = {

        # Compute
        "virtual machines": "Compute",
        "azure app service": "Compute",
        "azure functions": "Compute",
        "azure kubernetes service": "Compute",

        # Storage
        "storage": "Storage",
        "azure storage": "Storage",

        # Databases
        "sql database": "Databases",
        "azure sql database": "Databases",
        "azure database for postgresql": "Databases",
        "azure database for mysql": "Databases",

        # Networking
        "virtual network": "Networking",
        "azure dns": "Networking",

        # Analytics
        "azure synapse analytics": "Analytics",

        # AI / ML
        "azure machine learning":
            "AI and Machine Learning",
    }


    if "ServiceName" in df.columns:

        service_normalizado = (
            df["ServiceName"]
            .astype("string")
            .str.strip()
            .str.lower()
        )

        df["ServiceCategory"] = (
            service_normalizado
            .map(
                MAPA_SERVICE_CATEGORY
            )
            .fillna("Other")
        )

    else:

        df["ServiceCategory"] = "Other"


    # ============================================================
    # 19. TAGS
    # ============================================================

    def converter_tags_azure(tags_raw):

        if (
            pd.isna(tags_raw)
            or str(tags_raw).strip() == ""
        ):
            return json.dumps({})

        bruto = str(
            tags_raw
        ).strip()


        # Alguns exports podem fornecer:
        #
        # "environment":"production","team":"finops"
        #
        # sem as chaves externas.

        if not bruto.startswith("{"):
            bruto = (
                "{"
                + bruto
                + "}"
            )


        try:

            dicionario_tags = (
                json.loads(bruto)
            )

        except (
            json.JSONDecodeError,
            TypeError
        ):

            return json.dumps({})


        if not isinstance(
            dicionario_tags,
            dict
        ):
            return json.dumps({})


        return json.dumps(
            dicionario_tags,
            ensure_ascii=False
        )


    if "Tags" in df.columns:

        df["Tags"] = (
            df["Tags"]
            .apply(
                converter_tags_azure
            )
        )

    else:

        df["Tags"] = json.dumps({})


    # ============================================================
    # 20. GARANTE O SCHEMA SELECIONADO
    # ============================================================

    for coluna in COLUNAS_OFICIAIS_FOCUS:

        if coluna not in df.columns:
            df[coluna] = None


    # ============================================================
    # 21. RETORNO
    # ============================================================

    return df[
        COLUNAS_OFICIAIS_FOCUS
    ].copy()


if __name__ == "__main__":

    resultado = converter_azure(
        "data/input/custos_azure.csv"
    )

    print(resultado.head())