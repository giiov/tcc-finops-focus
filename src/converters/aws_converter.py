import json
import pandas as pd

from src.mapping.aws_mapping import AWS_MAPPING
from src.schemas.focus_schema import COLUNAS_OFICIAIS_FOCUS


def converter_aws(caminho_arquivo):

    df = pd.read_csv(caminho_arquivo)

    def coluna_numerica(nome_coluna):
        if nome_coluna in df.columns:
            return pd.to_numeric(
                df[nome_coluna],
                errors="coerce"
            )

        return pd.Series(
            float("nan"),
            index=df.index
        )

    if "lineItem/LineItemType" in df.columns:
        line_item_type = (
            df["lineItem/LineItemType"]
            .astype("string")
            .str.strip()
        )
    else:
        line_item_type = pd.Series(
            pd.NA,
            index=df.index,
            dtype="string"
        )


    public_on_demand_cost = coluna_numerica(
        "pricing/publicOnDemandCost"
    )

    reservation_effective_cost = coluna_numerica(
        "reservation/EffectiveCost"
    )

    reservation_unused_recurring_fee = coluna_numerica(
        "reservation/UnusedRecurringFee"
    )

    reservation_unused_amortized_upfront = coluna_numerica(
        "reservation/UnusedAmortizedUpfrontFeeForBillingPeriod"
    )

    savings_plan_effective_cost = coluna_numerica(
        "savingsPlan/SavingsPlanEffectiveCost"
    )

    savings_plan_total_commitment = coluna_numerica(
        "savingsPlan/TotalCommitmentToDate"
    )

    savings_plan_used_commitment = coluna_numerica(
        "savingsPlan/UsedCommitment"
    )

    df = df.rename(columns=AWS_MAPPING)

    for coluna in [
        "ChargePeriodStart",
        "ChargePeriodEnd",
        "BillingPeriodStart",
        "BillingPeriodEnd",
    ]:

        if coluna in df.columns:
            df[coluna] = pd.to_datetime(
                df[coluna],
                errors="coerce",
                utc=True
            )

    df["ServiceProviderName"] = "Amazon Web Services"
    df["HostProviderName"] = "Amazon Web Services"

    if "InvoiceIssuerName" not in df.columns:
        df["InvoiceIssuerName"] = None

    # O CUR fornece UsageAccountId, mas não derivamos
    # artificialmente o nome da conta.

    df["SubAccountName"] = None

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
    }

    df["ChargeCategory"] = line_item_type.map(
        MAPA_CHARGE_CATEGORY
    )

    # Refund permanece sem categoria porque o tipo da linha
    # não informa necessariamente a categoria econômica
    # original que está sendo devolvida.
    #
    # SavingsPlanNegation também permanece sem categoria,
    # pois é uma linha técnica usada pela AWS para compensar
    # o custo On-Demand da linha coberta.

    # LineItemType não é suficiente para determinar
    # genericamente a classe Correction do FOCUS.
    df["ChargeClass"] = None

    if "BilledCost" in df.columns:

        df["BilledCost"] = pd.to_numeric(
            df["BilledCost"],
            errors="coerce"
        )

    else:

        df["BilledCost"] = None

    df["EffectiveCost"] = df["BilledCost"]

    # DiscountedUsage representa uso coberto por RI.
    #
    # reservation/EffectiveCost contém o custo efetivo
    # da reserva alocado ao uso.

    mascara_ri_usage = line_item_type.eq(
        "DiscountedUsage"
    )

    mascara = (
        mascara_ri_usage
        & reservation_effective_cost.notna()
    )

    df.loc[
        mascara,
        "EffectiveCost"
    ] = reservation_effective_cost[mascara]

    mascara_ri_fee = line_item_type.eq(
        "RIFee"
    )

    custo_ri_nao_utilizado = (
        reservation_unused_amortized_upfront.fillna(0)
        +
        reservation_unused_recurring_fee.fillna(0)
    )

    possui_dado_ri_unused = (
        reservation_unused_amortized_upfront.notna()
        |
        reservation_unused_recurring_fee.notna()
    )

    mascara = (
        mascara_ri_fee
        & possui_dado_ri_unused
    )

    df.loc[
        mascara,
        "EffectiveCost"
    ] = custo_ri_nao_utilizado[mascara]


    # Se for RIFee mas os campos específicos não estiverem
    # disponíveis, não tratamos todo o valor faturado como
    # custo efetivo do período.

    df.loc[
        mascara_ri_fee & ~possui_dado_ri_unused,
        "EffectiveCost"
    ] = 0

    # SavingsPlanEffectiveCost contém a parcela do
    # compromisso atribuída à linha de uso coberto.

    mascara_sp_usage = line_item_type.eq(
        "SavingsPlanCoveredUsage"
    )

    mascara = (
        mascara_sp_usage
        & savings_plan_effective_cost.notna()
    )

    df.loc[
        mascara,
        "EffectiveCost"
    ] = savings_plan_effective_cost[mascara]

    # SavingsPlanNegation neutraliza o custo On-Demand
    # da linha SavingsPlanCoveredUsage.
    # Não representa custo efetivo adicional.

    mascara_sp_negation = line_item_type.eq(
        "SavingsPlanNegation"
    )

    df.loc[
        mascara_sp_negation,
        "EffectiveCost"
    ] = 0

    # O custo antecipado será reconhecido por meio das
    # linhas de uso/compromisso correspondentes.
    mascara_sp_upfront = line_item_type.eq(
        "SavingsPlanUpfrontFee"
    )

    df.loc[
        mascara_sp_upfront,
        "EffectiveCost"
    ] = 0

    mascara_sp_recurring = line_item_type.eq(
        "SavingsPlanRecurringFee"
    )

    possui_dado_sp = (
        savings_plan_total_commitment.notna()
        & savings_plan_used_commitment.notna()
    )

    compromisso_sp_nao_utilizado = (
        savings_plan_total_commitment
        -
        savings_plan_used_commitment
    )

    mascara = (
        mascara_sp_recurring
        & possui_dado_sp
    )

    df.loc[
        mascara,
        "EffectiveCost"
    ] = compromisso_sp_nao_utilizado[mascara]


    # Se a linha existir mas os campos necessários não
    # estiverem disponíveis, não inventamos a diferença.

    df.loc[
        mascara_sp_recurring & ~possui_dado_sp,
        "EffectiveCost"
    ] = 0


    df["ListCost"] = None

    tipos_consumo = [
        "Usage",
        "DiscountedUsage",
        "SavingsPlanCoveredUsage",
    ]

    mascara_consumo = line_item_type.isin(
        tipos_consumo
    )

    mascara = (
        mascara_consumo
        & public_on_demand_cost.notna()
    )

    df.loc[
        mascara,
        "ListCost"
    ] = public_on_demand_cost[mascara]

    df["ListCost"] = pd.to_numeric(
        df["ListCost"],
        errors="coerce"
    )


    df["ContractedCost"] = None

    if "PricingQuantity" in df.columns:

        df["PricingQuantity"] = pd.to_numeric(
            df["PricingQuantity"],
            errors="coerce"
        )

    else:

        df["PricingQuantity"] = None

    if "PricingUnit" not in df.columns:
        df["PricingUnit"] = None

    # Não inferimos ResourceType utilizando instanceType,
    # productFamily ou valores artificiais como "General".

    df["ResourceType"] = None

    MAPA_SERVICE_CATEGORY = {
        "amazon elastic compute cloud": "Compute",
        "amazon ec2": "Compute",

        "amazon simple storage service": "Storage",
        "amazon s3": "Storage",

        "amazon elastic block store": "Storage",

        "amazon relational database service": "Databases",
        "amazon rds": "Databases",

        "amazon dynamodb": "Databases",

        "amazon virtual private cloud": "Networking",
        "amazon vpc": "Networking",

        "aws lambda": "Compute",
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
            .map(MAPA_SERVICE_CATEGORY)
            .fillna("Other")
        )

    else:

        df["ServiceCategory"] = "Other"

    colunas_de_tags = [
        coluna
        for coluna in df.columns
        if coluna.startswith("resourceTags/user:")
    ]


    def montar_tags(linha):

        dicionario_tags = {}

        for coluna in colunas_de_tags:

            valor = linha[coluna]

            if (
                pd.notna(valor)
                and str(valor).strip() != ""
            ):

                chave = coluna.replace(
                    "resourceTags/user:",
                    "",
                    1
                )

                dicionario_tags[chave] = valor

        return json.dumps(
            dicionario_tags,
            ensure_ascii=False
        )


    if colunas_de_tags:

        df["Tags"] = df.apply(
            montar_tags,
            axis=1
        )

    else:

        df["Tags"] = json.dumps({})

    # Para Tax, quantidade/unidade de pricing não representam
    # consumo precificado no sentido utilizado pelo projeto.

    mascara_tax = line_item_type.eq(
        "Tax"
    )

    df.loc[
        mascara_tax,
        "PricingQuantity"
    ] = None

    df.loc[
        mascara_tax,
        "PricingUnit"
    ] = None

    for coluna in COLUNAS_OFICIAIS_FOCUS:

        if coluna not in df.columns:
            df[coluna] = None

    return df[
        COLUNAS_OFICIAIS_FOCUS
    ].copy()


if __name__ == "__main__":

    resultado = converter_aws(
        "data/input/custos_aws.csv"
    )

    print(resultado.head())