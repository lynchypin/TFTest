# service_integrations.tf
#
# Events API v2 integrations for each service - direct API access
# for any tool that can send HTTP requests.

# Events API v2 integration for each service (direct API access)
resource "pagerduty_service_integration" "events_api_v2" {
  for_each = { for s in local.services : s.name => s }

  name    = "Events API v2"
  service = pagerduty_service.services[each.key].id
  type    = "events_api_v2_inbound_integration"
}

# Output Events API v2 integration keys
output "service_integration_keys" {
  value = {
    for name, integration in pagerduty_service_integration.events_api_v2 :
    name => integration.integration_key
  }
  description = "Events API v2 integration keys for each service (direct incident creation)"
  sensitive   = true
}
