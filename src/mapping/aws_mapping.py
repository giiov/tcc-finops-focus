AWS_MAPPING = {
    #Descrição e Período de Cobrança
    "lineItem/LineItemDescription": "ChargeDescription",
    "lineItem/UsageStartDate": "ChargePeriodStart",
    "lineItem/UsageEndDate": "ChargePeriodEnd",

    #Contas de Faturamento e Entidades
    "bill/PayerAccountId": "BillingAccountId",
    "lineItem/UsageAccountId": "SubAccountId",
    "bill/BillingEntity": "PublisherName",

    #Custos e Moeda
    "lineItem/UnblendedCost": "BilledCost",
    "pricing/publicOnDemandCost": "EffectiveCost",
    "lineItem/CurrencyCode": "BillingCurrency",

    #Serviços e Recursos
    "lineItem/ResourceId": "ResourceId",
    "product/ProductName": "ServiceName",


}
