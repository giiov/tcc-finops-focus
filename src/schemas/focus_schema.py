COLUNAS_MANDATORY_FOCUS = [
    "BilledCost",
    "BillingAccountId",
    "BillingAccountName",
    "BillingCurrency",
    "BillingPeriodStart",
    "BillingPeriodEnd",
    "ChargeCategory",
    "ChargeClass",
    "ChargeDescription",
    "ChargePeriodStart",
    "ChargePeriodEnd",
    "ContractedCost",
    "EffectiveCost",
    "HostProviderName",
    "InvoiceIssuerName",
    "ListCost",
    "PricingQuantity",
    "PricingUnit",
    "ServiceProviderName",
    "ServiceCategory",
    "ServiceName",
]

COLUNAS_CONDITIONAL_FOCUS = [
    "ResourceId",
    "ResourceType",
    "SubAccountId",
    "SubAccountName",
    "Tags",
]

COLUNAS_OFICIAIS_FOCUS = (
    COLUNAS_MANDATORY_FOCUS
    + COLUNAS_CONDITIONAL_FOCUS
)