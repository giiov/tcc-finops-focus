AWS_MAPPING = {
    # Descrição
    "lineItem/LineItemDescription": "ChargeDescription",

    # Período da cobrança
    "lineItem/UsageStartDate": "ChargePeriodStart",
    "lineItem/UsageEndDate": "ChargePeriodEnd",

    # Período de faturamento
    "bill/BillingPeriodStartDate": "BillingPeriodStart",
    "bill/BillingPeriodEndDate": "BillingPeriodEnd",

    # Conta de faturamento
    "bill/PayerAccountId": "BillingAccountId",
    "bill/PayerAccountName": "BillingAccountName",

    # Subconta / conta de uso
    "lineItem/UsageAccountId": "SubAccountId",

    # Moeda
    "lineItem/CurrencyCode": "BillingCurrency",

    # Custo faturado
    "lineItem/UnblendedCost": "BilledCost",

    # Pricing
    "lineItem/UsageAmount": "PricingQuantity",
    "pricing/unit": "PricingUnit",

    # Serviço e recurso
    "lineItem/ResourceId": "ResourceId",
    "product/ProductName": "ServiceName",

    # Emissor da fatura
    "bill/InvoicingEntity": "InvoiceIssuerName",
}