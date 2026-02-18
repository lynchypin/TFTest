terraform {
  required_providers {
    pagerduty = {
      source  = "PagerDuty/pagerduty"
      version = "3.22.0"
    }
  }
  required_version = ">= 1.4.0"
}