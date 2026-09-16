ORACLE_MAPPING = {
    # Descrição e Período de Cobrança
    "product/description": "ChargeDescription",
    "lineItem/intervalUsageStart": "ChargePeriodStart",
    "lineItem/intervalUsageEnd": "ChargePeriodEnd",

    # Contas
    "cost/subscriptionId": "BillingAccountId",
    "lineItem/TenantId": "SubAccountId",

    # Moeda
    "cost/currencyCode": "BillingCurrency",

    # Custos
    "cost/myCost": "BilledCost",

    # Serviços e Recursos
    "product/resourceId": "ResourceId",
    "product/service": "ServiceName",
}