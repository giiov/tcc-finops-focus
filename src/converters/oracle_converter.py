import json
import pandas as pd

from src.mapping.oracle_mapping import ORACLE_MAPPING
from src.schemas.focus_schema import COLUNAS_OFICIAIS_FOCUS


def converter_oracle(caminho_arquivo):
    """
    Converte OCI Cost Reports para o subconjunto utilizado
    pelo projeto, baseado no FOCUS v1.4.

    O conversor evita inferir valores quando o relatório
    proprietário da OCI não fornece informação suficiente
    para determinar semanticamente um atributo FOCUS.
    """

    # ============================================================
    # 1. LEITURA
    # ============================================================

    df = pd.read_csv(caminho_arquivo)


    # ============================================================
    # 2. MAPEAMENTOS DIRETOS
    # ============================================================

    df = df.rename(columns=ORACLE_MAPPING)


    # ============================================================
    # 3. PROVEDOR
    # ============================================================

    df["ServiceProviderName"] = "Oracle"
    df["HostProviderName"] = "Oracle"
    df["InvoiceIssuerName"] = "Oracle"


    # ============================================================
    # 4. BILLING ACCOUNT NAME
    # ============================================================

    # O Cost Report proprietário utilizado como fonte
    # não fornece um nome correspondente de forma segura.

    df["BillingAccountName"] = None


    # ============================================================
    # 5. SUB ACCOUNT NAME
    # ============================================================

    # Temos o identificador da tenancy em SubAccountId,
    # mas não derivamos um nome quando ele não é fornecido
    # diretamente pela fonte selecionada.

    df["SubAccountName"] = None


    # ============================================================
    # 6. BILLING PERIOD
    # ============================================================

    # O período é derivado do mês em que o uso ocorreu.
    #
    # BillingPeriodStart = primeiro instante do mês
    # BillingPeriodEnd   = primeiro instante do mês seguinte

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


    # ============================================================
    # 7. CHARGE PERIOD END
    # ============================================================

    if "ChargePeriodEnd" in df.columns:

        df["ChargePeriodEnd"] = pd.to_datetime(
            df["ChargePeriodEnd"],
            errors="coerce",
            utc=True
        )

    else:

        df["ChargePeriodEnd"] = None


    # ============================================================
    # 8. CHARGE CATEGORY
    # ============================================================

    # O Cost Report proprietário utilizado pelo projeto
    # representa principalmente linhas de consumo.
    #
    # Para essas linhas, usamos Usage.
    #
    # IMPORTANTE:
    # lineItem/isCorrection NÃO altera automaticamente
    # ChargeCategory para Adjustment.
    #
    # ChargeCategory e ChargeClass representam conceitos
    # diferentes no FOCUS.

    df["ChargeCategory"] = "Usage"


    # ============================================================
    # 9. CHARGE CLASS
    # ============================================================

    # lineItem/isCorrection identifica uma linha de
    # correção/reversão no relatório da OCI.
    #
    # Mantemos essa informação separada da categoria
    # econômica da cobrança.

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


    # ============================================================
    # 10. BILLED COST
    # ============================================================

    # cost/myCost foi mapeado diretamente para BilledCost.

    if "BilledCost" in df.columns:

        df["BilledCost"] = pd.to_numeric(
            df["BilledCost"],
            errors="coerce"
        )

    else:

        df["BilledCost"] = None


    # ============================================================
    # 11. EFFECTIVE COST
    # ============================================================

    # No mapeamento oficial da Oracle para FOCUS,
    # cost/myCost é utilizado também como origem
    # para EffectiveCost no cenário suportado.

    df["EffectiveCost"] = df["BilledCost"]


    # ============================================================
    # 12. PRICING QUANTITY
    # ============================================================

    # usage/billedQuantity foi mapeado para PricingQuantity.

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

    # cost/skuUnitDescription foi mapeado para PricingUnit.

    if "PricingUnit" not in df.columns:
        df["PricingUnit"] = None


    # ============================================================
    # 14. CONTRACTED COST
    # ============================================================

    # O OCI Cost Report proprietário fornece cost/unitPrice,
    # definido pela Oracle como o preço faturado por unidade.
    #
    # A Oracle documenta a relação:
    #
    # cost/myCost =
    # usage/billedQuantity * cost/unitPrice
    #
    # Entretanto, cost/unitPrice não comprova, por si só,
    # que o valor corresponde ao ContractedUnitPrice
    # conceitual definido pelo FOCUS.
    #
    # Portanto, não fazemos:
    #
    # ContractedCost = BilledCost
    #
    # nem:
    #
    # ContractedCost = cost/unitPrice * PricingQuantity
    #
    # quando não é possível determinar com segurança
    # o preço contratado a partir da fonte selecionada.
    #
    # A coluna permanece estruturalmente presente,
    # mas semanticamente indisponível.

    df["ContractedCost"] = None


    # ============================================================
    # 15. LIST COST
    # ============================================================

    # O Cost Report proprietário utilizado pelo projeto
    # não fornece diretamente o ListCost do FOCUS.
    #
    # A tabela oficial de correspondência da Oracle não
    # fornece um mapeamento proprietário direto para
    # ListCost.
    #
    # O relatório FOCUS nativo da Oracle pode calcular
    # esse atributo utilizando informação de preço de lista,
    # mas essa informação não está diretamente disponível
    # na fonte proprietária selecionada pelo projeto.
    #
    # Portanto, não fazemos:
    #
    # ListCost = BilledCost
    #
    # pois isso poderia representar um preço já descontado
    # como se fosse o preço público/lista.
    #
    # A coluna permanece estruturalmente presente,
    # mas semanticamente indisponível.

    df["ListCost"] = None


    # ============================================================
    # 16. SERVICE NAME
    # ============================================================

    if "ServiceName" not in df.columns:
        df["ServiceName"] = None


    # ============================================================
    # 17. SERVICE CATEGORY
    # ============================================================

    # Classificação controlada adotada pelo projeto.
    #
    # Os nomes conhecidos são convertidos para categorias
    # utilizadas pelo schema baseado no FOCUS.
    #
    # Serviços não reconhecidos recebem Other.

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


    # ============================================================
    # 18. RESOURCE TYPE
    # ============================================================

    # O Cost Report proprietário selecionado não fornece
    # um ResourceType FOCUS diretamente.
    #
    # Também não inferimos o tipo a partir do ResourceId,
    # ServiceName ou ChargeDescription.

    df["ResourceType"] = None


    # ============================================================
    # 19. TAGS
    # ============================================================

    # No OCI Cost Report, tags podem aparecer como
    # colunas individuais prefixadas por "tags/".
    #
    # Exemplo:
    #
    # tags/environment
    # tags/team
    #
    # Todas são consolidadas em um único JSON.

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


    # ============================================================
    # 20. GARANTE O SCHEMA SELECIONADO
    # ============================================================

    # Mantemos todas as 26 colunas adotadas pelo projeto.
    #
    # Quando um atributo não pode ser obtido ou derivado
    # de forma semanticamente segura, sua coluna continua
    # presente e recebe None.

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

    resultado = converter_oracle(
        "data/input/custos_oracle.csv"
    )

    print(resultado.head())