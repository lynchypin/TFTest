############################################################
# maintenance_windows.tf — Maintenance Window Resources
############################################################

variable "enable_maintenance_windows" {
  type        = bool
  default     = false
  description = "Enable creation of maintenance window resources."
}

variable "maintenance_windows" {
  type = map(object({
    description = string
    services    = list(string)
    start_time  = string
    end_time    = string
  }))
  default     = {}
  description = "Map of maintenance windows to create. Times should be in ISO 8601 format."
}

# ========== PREDEFINED MAINTENANCE WINDOW TEMPLATES ==========
# These can be enabled by setting enable_maintenance_windows = true
# and providing specific start/end times in terraform.tfvars

locals {
  # Default maintenance window definitions (templates)
  default_maint_windows = {
    "weekly_platform_maintenance" = {
      description = "Weekly platform maintenance window - Kubernetes upgrades and patches"
      services    = ["Platform - Kubernetes/Platform", "Platform - Networking"]
    }
    "database_maintenance" = {
      description = "Database maintenance window - Backups, vacuuming, and minor upgrades"
      services    = ["Platform - DBRE"]
    }
    "streaming_maintenance" = {
      description = "Streaming infrastructure maintenance - Kafka broker rolling updates"
      services    = ["Data - Streaming"]
    }
    "release_deployment" = {
      description = "Production release deployment window"
      services    = ["App - Orders API Team", "App - Checkout Team", "App - Identity Team"]
    }
  }
}

# ========== MAINTENANCE WINDOWS ==========
resource "pagerduty_maintenance_window" "windows" {
  for_each = var.enable_maintenance_windows ? var.maintenance_windows : {}

  description = each.value.description
  start_time  = each.value.start_time
  end_time    = each.value.end_time

  services = [
    for svc_name in each.value.services : pagerduty_service.services[svc_name].id
  ]
}

# ========== EXAMPLE USAGE IN terraform.tfvars ==========
# maintenance_windows = {
#   "weekly_platform_maintenance" = {
#     description = "Weekly platform maintenance window"
#     services    = ["Platform - Kubernetes/Platform", "Platform - Networking"]
#     start_time  = "2024-01-28T02:00:00-05:00"
#     end_time    = "2024-01-28T06:00:00-05:00"
#   }
#   "database_maintenance" = {
#     description = "Database maintenance window"
#     services    = ["Platform - DBRE"]
#     start_time  = "2024-01-29T03:00:00-05:00"
#     end_time    = "2024-01-29T05:00:00-05:00"
#   }
# }
