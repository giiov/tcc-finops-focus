GCP_MAPPING = {
    #Descrição e Período de Cobrança
    "sku.description": "ChargeDescription",
    "usage_start_time": "ChargePeriodStart",
    "usage_end_time": "ChargePeriodEnd",

    #Contas
    "billing_account_id": "BillingAccountId",
    "project.id": "SubAccountId",

    #Custos e Moeda
    "cost": "BilledCost",
    "currency": "BillingCurrency",

    #Serviços e Recursos
    "service.description": "ServiceName",
}