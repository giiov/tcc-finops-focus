AZURE_MAPPING = {
    # Descrição e Período de Cobrança
    "ProductName": "ChargeDescription",
    "Date": "ChargePeriodStart",
    "BillingPeriodStartDate": "BillingPeriodStart",

    # Contas
    "BillingProfileId": "BillingAccountId",
    "BillingProfileName": "BillingAccountName",
    "SubscriptionId": "SubAccountId",

    # Recursos
    "ResourceId": "ResourceId",
    "ResourceType": "ResourceType",

    # Moeda
    "BillingCurrency": "BillingCurrency",

    # Serviços e Recursos
    "PublisherName": "PublisherName",

    # Custos
    # Alguns exports simplificados do Azure usam estes nomes equivalentes.
    "PreTaxCost": "CostInBillingCurrency",
    "ResourceRate": "UnitPrice",
    "UsageQuantity": "Quantity",
    "PaygCostInBillingCurrency": "ListCost",
}