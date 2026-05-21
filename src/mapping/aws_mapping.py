AWS_MAPPING = {
    "identity/LineItemId": "ChargeId",
    "lineItem/LineItemDescription": "ChargeDescription",
    "lineItem/UsageStartDate": "ChargePeriodStart",
    "lineItem/UsageEndDate": "ChargePeriodEnd",
    "bill/PayerAccountId": "BillingAccountId",
    "lineItem/UsageAccountId": "SubAccountId",
    "lineItem/LineItemType": "ChargeCategory",
    "lineItem/UnblendedCost": "BilledCost",
    "pricing/publicOnDemandCost": "EffectiveCost",
    "bill/BillingEntity": "BillingCurrency",
    "lineItem/ResourceId": "ResourceId",
    "product/instanceType": "ResourceType",
    "product/ProductName": "ServiceName",
    "resourceTags/user:Environment": "Tags"
}
