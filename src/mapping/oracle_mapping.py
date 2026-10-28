ORACLE_MAPPING = {
    # Descrição
    "product/description": "ChargeDescription",

    # Período da cobrança
    "lineItem/intervalUsageStart": "ChargePeriodStart",
    "lineItem/intervalUsageEnd": "ChargePeriodEnd",

    # Conta de faturamento
    "cost/subscriptionId": "BillingAccountId",

    # Subconta / tenancy
    "lineItem/TenantId": "SubAccountId",

    # Moeda
    "cost/currencyCode": "BillingCurrency",

    # Custos
    "cost/myCost": "BilledCost",

    # Pricing
    "usage/billedQuantity": "PricingQuantity",
    "cost/skuUnitDescription": "PricingUnit",

    # Serviço e recurso
    "product/resourceId": "ResourceId",
    "product/service": "ServiceName",
}