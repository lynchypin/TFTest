resource "pagerduty_team" "platform" {
  name        = "Platform Engineering"
  description = "Platform and infrastructure team"
}

data "pagerduty_priority" "p1" {
  name = "P1"
}

data "pagerduty_priority" "p2" {
  name = "P2"
}

data "pagerduty_priority" "p3" {
  name = "P3"
}

resource "pagerduty_escalation_policy" "ep_major_incident" {
  name      = "Major Incident Escalation"
  num_loops = 9
  teams     = [pagerduty_team.platform.id]
  rule {
    escalation_delay_in_minutes = 5
    target {
      type = "schedule_reference"
      id   = pagerduty_schedule.oncall_primary.id
    }
  }
}

resource "pagerduty_escalation_policy" "ep_soc" {
  name      = "SOC Escalation"
  num_loops = 9
  teams     = [pagerduty_team.platform.id]
  rule {
    escalation_delay_in_minutes = 5
    target {
      type = "schedule_reference"
      id   = pagerduty_schedule.oncall_primary.id
    }
  }
}

resource "pagerduty_escalation_policy" "ep_platform" {
  name      = "Platform Team Escalation"
  num_loops = 3
  teams     = [pagerduty_team.platform.id]
  rule {
    escalation_delay_in_minutes = 10
    target {
      type = "schedule_reference"
      id   = pagerduty_schedule.oncall_primary.id
    }
  }
}

resource "pagerduty_escalation_policy" "ep_dba" {
  name      = "DBA Escalation"
  num_loops = 3
  teams     = [pagerduty_team.platform.id]
  rule {
    escalation_delay_in_minutes = 10
    target {
      type = "schedule_reference"
      id   = pagerduty_schedule.oncall_primary.id
    }
  }
}

resource "pagerduty_escalation_policy" "ep_customer_success" {
  name      = "Customer Success Escalation"
  num_loops = 2
  teams     = [pagerduty_team.platform.id]
  rule {
    escalation_delay_in_minutes = 15
    target {
      type = "schedule_reference"
      id   = pagerduty_schedule.oncall_primary.id
    }
  }
}

resource "pagerduty_escalation_policy" "ep_support" {
  name      = "Support Escalation"
  num_loops = 3
  teams     = [pagerduty_team.platform.id]
  rule {
    escalation_delay_in_minutes = 10
    target {
      type = "schedule_reference"
      id   = pagerduty_schedule.oncall_primary.id
    }
  }
}

resource "pagerduty_escalation_policy" "ep_payments" {
  name      = "Payments Team Escalation"
  num_loops = 3
  teams     = [pagerduty_team.platform.id]
  rule {
    escalation_delay_in_minutes = 5
    target {
      type = "schedule_reference"
      id   = pagerduty_schedule.oncall_primary.id
    }
  }
}

resource "pagerduty_escalation_policy" "ep_identity" {
  name      = "Identity Team Escalation"
  num_loops = 3
  teams     = [pagerduty_team.platform.id]
  rule {
    escalation_delay_in_minutes = 5
    target {
      type = "schedule_reference"
      id   = pagerduty_schedule.oncall_primary.id
    }
  }
}

resource "pagerduty_escalation_policy" "ep_data" {
  name      = "Data Engineering Escalation"
  num_loops = 3
  teams     = [pagerduty_team.platform.id]
  rule {
    escalation_delay_in_minutes = 10
    target {
      type = "schedule_reference"
      id   = pagerduty_schedule.oncall_primary.id
    }
  }
}

resource "pagerduty_schedule" "oncall_primary" {
  name      = "Primary On-Call Schedule"
  time_zone = "America/New_York"
  layer {
    name                         = "Layer 1"
    start                        = "2024-01-01T00:00:00-05:00"
    rotation_virtual_start       = "2024-01-01T00:00:00-05:00"
    rotation_turn_length_seconds = 604800
    users = [
      data.pagerduty_user.by_email["jbeam@losandesgaa.onmicrosoft.com"].id,
      data.pagerduty_user.by_email["jcasker@losandesgaa.onmicrosoft.com"].id,
      data.pagerduty_user.by_email["aguiness@losandesgaa.onmicrosoft.com"].id,
      data.pagerduty_user.by_email["jcuervo@losandesgaa.onmicrosoft.com"].id,
      data.pagerduty_user.by_email["jdaniels@losandesgaa.onmicrosoft.com"].id,
      data.pagerduty_user.by_email["gtonic@losandesgaa.onmicrosoft.com"].id,
    ]
  }
}

resource "pagerduty_service" "svc_k8s" {
  name                    = "Kubernetes Platform"
  description             = "Kubernetes cluster and orchestration"
  escalation_policy       = pagerduty_escalation_policy.ep_platform.id
  auto_resolve_timeout    = 14400
  acknowledgement_timeout = 1800
}

resource "pagerduty_service" "svc_dbre" {
  name                    = "Database Reliability"
  description             = "Database systems and reliability"
  escalation_policy       = pagerduty_escalation_policy.ep_dba.id
  auto_resolve_timeout    = 14400
  acknowledgement_timeout = 1800
}

resource "pagerduty_service" "svc_net" {
  name                    = "Network Infrastructure"
  description             = "Network and connectivity"
  escalation_policy       = pagerduty_escalation_policy.ep_platform.id
  auto_resolve_timeout    = 14400
  acknowledgement_timeout = 1800
}

resource "pagerduty_service" "svc_security_orch" {
  name                    = "Security Operations"
  description             = "Security monitoring and incident response"
  escalation_policy       = pagerduty_escalation_policy.ep_soc.id
  auto_resolve_timeout    = 14400
  acknowledgement_timeout = 1800
}

resource "pagerduty_service" "svc_payments_orch" {
  name                    = "Payments Platform"
  description             = "Payment processing systems"
  escalation_policy       = pagerduty_escalation_policy.ep_payments.id
  auto_resolve_timeout    = 14400
  acknowledgement_timeout = 1800
}

resource "pagerduty_service" "svc_orders_orch" {
  name                    = "Order Management"
  description             = "Order processing and fulfillment"
  escalation_policy       = pagerduty_escalation_policy.ep_platform.id
  auto_resolve_timeout    = 14400
  acknowledgement_timeout = 1800
}

resource "pagerduty_service" "svc_checkout_orch" {
  name                    = "Checkout Platform"
  description             = "Checkout and cart systems"
  escalation_policy       = pagerduty_escalation_policy.ep_platform.id
  auto_resolve_timeout    = 14400
  acknowledgement_timeout = 1800
}

resource "pagerduty_service" "svc_identity_orch" {
  name                    = "Identity Platform"
  description             = "Authentication and identity services"
  escalation_policy       = pagerduty_escalation_policy.ep_identity.id
  auto_resolve_timeout    = 14400
  acknowledgement_timeout = 1800
}

resource "pagerduty_service" "svc_streaming_orch" {
  name                    = "Data Streaming"
  description             = "Kafka and streaming infrastructure"
  escalation_policy       = pagerduty_escalation_policy.ep_data.id
  auto_resolve_timeout    = 14400
  acknowledgement_timeout = 1800
}

resource "pagerduty_service" "svc_analytics_orch" {
  name                    = "Analytics Platform"
  description             = "Data analytics and reporting"
  escalation_policy       = pagerduty_escalation_policy.ep_data.id
  auto_resolve_timeout    = 14400
  acknowledgement_timeout = 1800
}

resource "pagerduty_service" "svc_analytics" {
  name                    = "Analytics Service"
  description             = "Analytics data service"
  escalation_policy       = pagerduty_escalation_policy.ep_data.id
  auto_resolve_timeout    = 14400
  acknowledgement_timeout = 1800
}

resource "pagerduty_service" "svc_orders" {
  name                    = "Orders Service"
  description             = "Order processing service"
  escalation_policy       = pagerduty_escalation_policy.ep_platform.id
  auto_resolve_timeout    = 14400
  acknowledgement_timeout = 1800
}

resource "pagerduty_service" "svc_checkout" {
  name                    = "Checkout Service"
  description             = "Checkout processing service"
  escalation_policy       = pagerduty_escalation_policy.ep_platform.id
  auto_resolve_timeout    = 14400
  acknowledgement_timeout = 1800
}

resource "pagerduty_service" "svc_identity" {
  name                    = "Identity Service"
  description             = "Identity management service"
  escalation_policy       = pagerduty_escalation_policy.ep_identity.id
  auto_resolve_timeout    = 14400
  acknowledgement_timeout = 1800
}

resource "pagerduty_service" "svc_streaming" {
  name                    = "Streaming Service"
  description             = "Streaming data service"
  escalation_policy       = pagerduty_escalation_policy.ep_data.id
  auto_resolve_timeout    = 14400
  acknowledgement_timeout = 1800
}

resource "pagerduty_escalation_policy" "ep_compliance" {
  name      = "Compliance Escalation"
  num_loops = 2
  teams     = [pagerduty_team.platform.id]
  rule {
    escalation_delay_in_minutes = 5
    target {
      type = "schedule_reference"
      id   = pagerduty_schedule.oncall_primary.id
    }
  }
}

resource "pagerduty_escalation_policy" "ep_executive" {
  name      = "Executive Escalation"
  num_loops = 1
  teams     = [pagerduty_team.platform.id]
  rule {
    escalation_delay_in_minutes = 3
    target {
      type = "schedule_reference"
      id   = pagerduty_schedule.oncall_primary.id
    }
  }
}

resource "pagerduty_escalation_policy" "ep_noc" {
  name      = "Network Operations Center Escalation"
  num_loops = 3
  teams     = [pagerduty_team.platform.id]
  rule {
    escalation_delay_in_minutes = 10
    target {
      type = "schedule_reference"
      id   = pagerduty_schedule.oncall_primary.id
    }
  }
}

locals {
  extended_services = {
    k8s       = pagerduty_service.svc_k8s
    dbre      = pagerduty_service.svc_dbre
    net       = pagerduty_service.svc_net
    security  = pagerduty_service.svc_security_orch
    payments  = pagerduty_service.svc_payments_orch
    orders    = pagerduty_service.svc_orders_orch
    checkout  = pagerduty_service.svc_checkout_orch
    identity  = pagerduty_service.svc_identity_orch
    streaming = pagerduty_service.svc_streaming_orch
    analytics = pagerduty_service.svc_analytics_orch
  }
}
