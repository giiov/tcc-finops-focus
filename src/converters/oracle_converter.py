import json
import pandas as pd

from src.mapping.oracle_mapping import ORACLE_MAPPING
from src.schemas.focus_schema import COLUNAS_OFICIAIS_FOCUS


def converter_oracle(caminho_arquivo):

    df = pd.read_csv(caminho_arquivo)

    df = df.rename(columns=ORACLE_MAPPING)

    df["ServiceProviderName"] = "Oracle"
    df["HostProviderName"] = "Oracle"
    df["InvoiceIssuerName"] = "Oracle"


    df["BillingAccountName"] = None

    df["SubAccountName"] = None



    if "ChargePeriodStart" in df.columns:

        datas_uso = pd.to_datetime(
            df["ChargePeriodStart"],
            errors="coerce",
            utc=True
        )

        df["ChargePeriodStart"] = datas_uso

        df["BillingPeriodStart"] = (
            datas_uso
            .dt.to_period("M")
            .dt.start_time
            .dt.tz_localize("UTC")
        )

        df["BillingPeriodEnd"] = (
            df["BillingPeriodStart"]
            + pd.offsets.MonthBegin(1)
        )

    else:

        df["ChargePeriodStart"] = None
        df["BillingPeriodStart"] = None
        df["BillingPeriodEnd"] = None


    if "ChargePeriodEnd" in df.columns:

        df["ChargePeriodEnd"] = pd.to_datetime(
            df["ChargePeriodEnd"],
            errors="coerce",
            utc=True
        )

    else:

        df["ChargePeriodEnd"] = None

    df["ChargeCategory"] = "Usage"

    if "lineItem/isCorrection" in df.columns:

        eh_correcao = (
            df["lineItem/isCorrection"]
            .astype("string")
            .str.strip()
            .str.lower()
            .eq("true")
        )

        df["ChargeClass"] = None

        df.loc[
            eh_correcao,
            "ChargeClass"
        ] = "Correction"

    else:

        df["ChargeClass"] = None

    # cost/myCost foi mapeado diretamente para BilledCost.

    if "BilledCost" in df.columns:

        df["BilledCost"] = pd.to_numeric(
            df["BilledCost"],
            errors="coerce"
        )

    else:

        df["BilledCost"] = None

    df["EffectiveCost"] = df["BilledCost"]


    # usage/billedQuantity foi mapeado para PricingQuantity.

    if "PricingQuantity" in df.columns:

        df["PricingQuantity"] = pd.to_numeric(
            df["PricingQuantity"],
            errors="coerce"
        )

    else:

        df["PricingQuantity"] = None

    # cost/skuUnitDescription foi mapeado para PricingUnit.

    if "PricingUnit" not in df.columns:
        df["PricingUnit"] = None


    df["ContractedCost"] = None


    df["ListCost"] = None

    if "ServiceName" not in df.columns:
        df["ServiceName"] = None


    MAPA_SERVICE_CATEGORY = {
        "compute": "Compute",

        "object storage": "Storage",
        "block storage": "Storage",

        "database": "Databases",
        "autonomous database": "Databases",

        "networking": "Networking",
        "virtual cloud network": "Networking",
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


    df["ResourceType"] = None

    colunas_de_tags = [
        coluna
        for coluna in df.columns
        if coluna.startswith("tags/")
    ]


    def montar_tags(linha):

        dicionario_tags = {}

        for coluna in colunas_de_tags:

            valor = linha[coluna]

            if (
                pd.notna(valor)
                and str(valor).strip() != ""
            ):

                # Remove apenas o primeiro prefixo "tags/".
                chave = coluna.replace(
                    "tags/",
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

    for coluna in COLUNAS_OFICIAIS_FOCUS:

        if coluna not in df.columns:
            df[coluna] = None

    return df[
        COLUNAS_OFICIAIS_FOCUS
    ].copy()


if __name__ == "__main__":

    resultado = converter_oracle(
        "data/input/custos_oracle.csv"
    )

    print(resultado.head())