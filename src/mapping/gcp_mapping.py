GCP_MAPPING = {
    # Identificação da conta
    "billing_account_id": "BillingAccountId",

    # Subconta / projeto
    "project.id": "SubAccountId",
    "project.name": "SubAccountName",

    # Moeda
    "currency": "BillingCurrency",

    # Serviço e descrição da cobrança
    "service.description": "ServiceName",
    "sku.description": "ChargeDescription",

    # Período da cobrança
    "usage_start_time": "ChargePeriodStart",
    "usage_end_time": "ChargePeriodEnd",

    # Pricing
    "price.pricing_unit_quantity": "PricingQuantity",
    "price.unit": "PricingUnit",

    # Custo de lista
    "cost_at_list": "ListCost",
}