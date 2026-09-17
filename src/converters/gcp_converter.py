import json
import pandas as pd

from src.mapping.gcp_mapping import GCP_MAPPING
from src.schemas.focus_schema import COLUNAS_OFICIAIS_FOCUS


def converter_gcp(caminho_arquivo):
    """
    Converte o Google Cloud Standard Usage Cost Export
    para o subconjunto de colunas utilizado pelo projeto,
    baseado no FOCUS v1.4.

    Observação:
    O Google Cloud Standard Export não fornece informação
    suficiente para preencher semanticamente todos os campos
    obrigatórios do FOCUS. Campos sem correspondência segura
    permanecem nulos.
    """

    # ============================================================
    # 1. LEITURA
    # ============================================================

    df = pd.read_csv(caminho_arquivo)


    # ============================================================
    # 2. MAPEAMENTOS DIRETOS
    # ============================================================

    df = df.rename(columns=GCP_MAPPING)


    # ============================================================
    # 3. PROVEDOR
    # ============================================================

    df["ServiceProviderName"] = "Google Cloud"
    df["HostProviderName"] = "Google Cloud"


    # ============================================================
    # 4. CAMPOS NÃO DISPONÍVEIS DE FORMA SEGURA
    # ============================================================

    # O Standard Export não fornece um nome da conta de
    # faturamento correspondente a BillingAccountName.
    df["BillingAccountName"] = None

    # O Standard Export não fornece InvoiceIssuerName.
    df["InvoiceIssuerName"] = None

    # O Google não fornece ServiceCategory no export utilizado.
    # Não classificamos serviços manualmente para evitar
    # introduzir uma taxonomia criada pelo projeto.
    df["ServiceCategory"] = None

    # O Standard Export não possui granularidade de recurso
    # suficiente para ResourceId e ResourceType.
    df["ResourceId"] = None
    df["ResourceType"] = None


    # ============================================================
    # 5. BILLING PERIOD
    # ============================================================

    if "invoice.month" in df.columns:

        mes_fatura = pd.to_datetime(
            df["invoice.month"].astype(str),
            format="%Y%m",
            errors="coerce"
        )

        df["BillingPeriodStart"] = mes_fatura

        df["BillingPeriodEnd"] = (
            mes_fatura + pd.offsets.MonthBegin(1)
        )

    else:

        df["BillingPeriodStart"] = None
        df["BillingPeriodEnd"] = None


    # ============================================================
    # 6. CHARGE PERIOD
    # ============================================================

    if "ChargePeriodStart" in df.columns:

        df["ChargePeriodStart"] = pd.to_datetime(
            df["ChargePeriodStart"],
            errors="coerce",
            utc=True
        )

    if "ChargePeriodEnd" in df.columns:

        df["ChargePeriodEnd"] = pd.to_datetime(
            df["ChargePeriodEnd"],
            errors="coerce",
            utc=True
        )


    # ============================================================
    # 7. CHARGE CATEGORY
    # ============================================================

    MAPA_CHARGE_CATEGORY = {
        "regular": "Usage",
        "tax": "Tax",
        "adjustment": "Adjustment",
        "rounding_error": "Adjustment",
    }

    if "cost_type" in df.columns:

        cost_type_normalizado = (
            df["cost_type"]
            .astype("string")
            .str.strip()
            .str.lower()
            .str.replace(" ", "_", regex=False)
        )

        df["ChargeCategory"] = (
            cost_type_normalizado.map(
                MAPA_CHARGE_CATEGORY
            )
        )

    else:

        df["ChargeCategory"] = None


    # ============================================================
    # 8. CHARGE CLASS
    # ============================================================

    # ChargeClass = Correction deve representar correção
    # de período previamente faturado.
    #
    # adjustment_info.type sozinho informa o tipo do ajuste,
    # mas não é suficiente para provar que a cobrança pertence
    # a um período previamente fechado.
    #
    # Portanto, nesta conversão do Standard Export,
    # não inferimos Correction apenas pelo tipo do ajuste.

    df["ChargeClass"] = None


    # ============================================================
    # 9. FUNÇÃO PARA CALCULAR COST + CREDITS
    # ============================================================

    def calcular_custo_com_creditos(linha):

        custo_base = pd.to_numeric(
            linha.get("cost"),
            errors="coerce"
        )

        if pd.isna(custo_base):
            return None

        creditos_raw = linha.get(
            "credits",
            "[]"
        )

        if pd.isna(creditos_raw):
            return custo_base

        if isinstance(creditos_raw, list):

            lista_creditos = creditos_raw

        else:

            texto = str(
                creditos_raw
            ).strip()

            if texto in ("", "[]"):
                return custo_base

            try:

                lista_creditos = json.loads(
                    texto
                )

            except (
                json.JSONDecodeError,
                TypeError
            ):

                return custo_base

        if not isinstance(
            lista_creditos,
            list
        ):
            return custo_base

        soma_creditos = 0.0

        for credito in lista_creditos:

            if not isinstance(
                credito,
                dict
            ):
                continue

            valor = pd.to_numeric(
                credito.get("amount"),
                errors="coerce"
            )

            if not pd.isna(valor):
                soma_creditos += valor

        return custo_base + soma_creditos


    # ============================================================
    # 10. BILLED COST
    # ============================================================

    if "cost" in df.columns:

        df["BilledCost"] = df.apply(
            calcular_custo_com_creditos,
            axis=1
        )

    else:

        df["BilledCost"] = None


    # ============================================================
    # 11. EFFECTIVE COST
    # ============================================================

    # O mapeamento publicado pelo Google para seu FOCUS Export
    # utiliza cost + credits.amount também para EffectiveCost.
    #
    # Mantemos a mesma transformação para o subconjunto do projeto.

    if "cost" in df.columns:

        df["EffectiveCost"] = df.apply(
            calcular_custo_com_creditos,
            axis=1
        )

    else:

        df["EffectiveCost"] = None


    # ============================================================
    # 12. CONTRACTED COST
    # ============================================================

    # Mapeamento oficial publicado pelo Google:
    #
    # cost -> ContractedCost

    if "cost" in df.columns:

        df["ContractedCost"] = pd.to_numeric(
            df["cost"],
            errors="coerce"
        )

    else:

        df["ContractedCost"] = None


    # ============================================================
    # 13. LIST COST
    # ============================================================

    # Mapeamento oficial:
    #
    # cost_at_list -> ListCost

    if "ListCost" in df.columns:

        df["ListCost"] = pd.to_numeric(
            df["ListCost"],
            errors="coerce"
        )

    else:

        df["ListCost"] = None


    # ============================================================
    # 14. PRICING QUANTITY
    # ============================================================

    # Mapeamento oficial:
    #
    # price.pricing_unit_quantity
    #           ->
    # PricingQuantity

    if "PricingQuantity" in df.columns:

        df["PricingQuantity"] = pd.to_numeric(
            df["PricingQuantity"],
            errors="coerce"
        )

    else:

        df["PricingQuantity"] = None


    # ============================================================
    # 15. PRICING UNIT
    # ============================================================

    # Mapeamento oficial:
    #
    # price.unit -> PricingUnit

    if "PricingUnit" not in df.columns:
        df["PricingUnit"] = None


    # ============================================================
    # 16. TAGS
    # ============================================================

    def converter_labels_para_tags(
        labels_raw
    ):

        if pd.isna(labels_raw):
            return json.dumps({})

        if isinstance(
            labels_raw,
            list
        ):

            lista_labels = labels_raw

        else:

            texto = str(
                labels_raw
            ).strip()

            if texto in ("", "[]"):
                return json.dumps({})

            try:

                lista_labels = json.loads(
                    texto
                )

            except (
                json.JSONDecodeError,
                TypeError
            ):

                return json.dumps({})

        if not isinstance(
            lista_labels,
            list
        ):
            return json.dumps({})

        resultado = {}

        for item in lista_labels:

            if not isinstance(
                item,
                dict
            ):
                continue

            chave = item.get("key")
            valor = item.get("value")

            if (
                chave is not None
                and valor is not None
            ):

                resultado[
                    str(chave)
                ] = str(valor)

        return json.dumps(
            resultado,
            ensure_ascii=False
        )


    if "labels" in df.columns:

        df["Tags"] = df[
            "labels"
        ].apply(
            converter_labels_para_tags
        )

    else:

        df["Tags"] = json.dumps({})


    # ============================================================
    # 17. GARANTE A ESTRUTURA DO SCHEMA DO PROJETO
    # ============================================================

    for coluna in COLUNAS_OFICIAIS_FOCUS:

        if coluna not in df.columns:
            df[coluna] = None


    # ============================================================
    # 18. RETORNO
    # ============================================================

    return df[
        COLUNAS_OFICIAIS_FOCUS
    ].copy()