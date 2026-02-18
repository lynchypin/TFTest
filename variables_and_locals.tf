variable "tz" {
  description = "Default time zone for schedules"
  type        = string
  default     = "America/Santiago"
}

variable "rotation_start" {
  description = "RFC3339 start time for schedule rotations"
  type        = string
  default     = "2024-01-06T10:00:00-03:00"
}

variable "runbook_base_url" {
  description = "Base URL for runbook documentation"
  type        = string
  default     = "https://docs.losandes.internal/runbooks"
}

locals {
  demo_users = {
    jim_beam        = "jbeam@losandesgaa.onmicrosoft.com"
    jack_daniels    = "jdaniels@losandesgaa.onmicrosoft.com"
    jameson_casker  = "jcasker@losandesgaa.onmicrosoft.com"
    jose_cuervo     = "jcuervo@losandesgaa.onmicrosoft.com"
    ginny_tonic     = "gtonic@losandesgaa.onmicrosoft.com"
    arthur_guinness = "aguiness@losandesgaa.onmicrosoft.com"
  }

  schedules = {
    "Schedule - App Team" = {
      team          = "App"
      time_zone     = var.tz
      rotation_days = 7
      members = [
        local.demo_users.jim_beam,
        local.demo_users.jameson_casker,
      ]
      business_hours = null
    }

    "Schedule - Platform Team" = {
      team          = "Platform"
      time_zone     = var.tz
      rotation_days = 7
      members = [
        local.demo_users.jack_daniels,
        local.demo_users.jose_cuervo,
      ]
      business_hours = null
    }

    "Schedule - Data Team" = {
      team          = "Platform"
      time_zone     = var.tz
      rotation_days = 7
      members = [
        local.demo_users.jameson_casker,
        local.demo_users.arthur_guinness,
      ]
      business_hours = null
    }

    "Schedule - SecOps Team" = {
      team          = "SecOps"
      time_zone     = var.tz
      rotation_days = 7
      members = [
        local.demo_users.jose_cuervo,
        local.demo_users.ginny_tonic,
      ]
      business_hours = null
    }

    "Schedule - IT Support Team" = {
      team          = "Support"
      time_zone     = var.tz
      rotation_days = 7
      members = [
        local.demo_users.ginny_tonic,
        local.demo_users.jim_beam,
      ]
      business_hours = null
    }

    "Schedule - Business Ops Team" = {
      team          = "Support"
      time_zone     = var.tz
      rotation_days = 7
      members = [
        local.demo_users.arthur_guinness,
        local.demo_users.jack_daniels,
      ]
      business_hours = null
    }

    "Schedule - Manager Escalation" = {
      team          = "Platform"
      time_zone     = var.tz
      rotation_days = 7
      members = [
        local.demo_users.arthur_guinness,
        local.demo_users.jack_daniels,
        local.demo_users.ginny_tonic,
      ]
      business_hours = null
    }
  }

  escalation_policies = {
    "EP - Customer-Facing Apps" = [
      { delay = 1, schedule = "Schedule - App Team" },
      { delay = 15, schedule = "Schedule - Manager Escalation" },
    ]

    "EP - Platform Core" = [
      { delay = 1, schedule = "Schedule - Platform Team" },
      { delay = 15, schedule = "Schedule - Manager Escalation" },
    ]

    "EP - Data Services" = [
      { delay = 1, schedule = "Schedule - Data Team" },
      { delay = 15, schedule = "Schedule - Manager Escalation" },
    ]

    "EP - IT and Internal Apps" = [
      { delay = 1, schedule = "Schedule - IT Support Team" },
      { delay = 15, schedule = "Schedule - Manager Escalation" },
    ]

    "EP - Security Monitoring (SOC)" = [
      { delay = 1, schedule = "Schedule - SecOps Team" },
      { delay = 15, schedule = "Schedule - Manager Escalation" },
    ]

    "EP - Business Ops - Manual Operation" = [
      { delay = 1, schedule = "Schedule - Business Ops Team" },
      { delay = 15, schedule = "Schedule - Manager Escalation" },
    ]
  }

  services = [
    {
      name        = "Platform - DBRE"
      team        = "Platform"
      ep          = "EP - Platform Core"
      description = "Database Reliability Engineering - PostgreSQL, Redis, MySQL"
      runbook_url = "${var.runbook_base_url}/platform/dbre"
    },
    {
      name        = "Data - Streaming"
      team        = "Platform"
      ep          = "EP - Data Services"
      description = "Kafka, event streaming, real-time data pipelines"
      runbook_url = "${var.runbook_base_url}/data/streaming"
    },
    {
      name        = "Data - Analytics"
      team        = "Platform"
      ep          = "EP - Data Services"
      description = "Data warehouse, BI, analytics infrastructure"
      runbook_url = "${var.runbook_base_url}/data/analytics"
    },
    {
      name        = "SecOps"
      team        = "SecOps"
      ep          = "EP - Security Monitoring (SOC)"
      description = "Security operations, threat detection, incident response"
      runbook_url = "${var.runbook_base_url}/security/secops"
    },
    {
      name        = "Corp IT"
      team        = "Corp IT"
      ep          = "EP - IT and Internal Apps"
      description = "Corporate IT infrastructure, internal tools"
      runbook_url = "${var.runbook_base_url}/it/corp-it"
    },
    {
      name        = "Support"
      team        = "Support"
      ep          = "EP - IT and Internal Apps"
      description = "Customer support systems and tools"
      runbook_url = "${var.runbook_base_url}/support/general"
    },
    {
      name        = "Payments Ops"
      team        = "Support"
      ep          = "EP - Business Ops - Manual Operation"
      description = "Payment processing, vendor integrations"
      runbook_url = "${var.runbook_base_url}/payments/ops"
    },
    {
      name        = "App - Checkout Team"
      team        = "App"
      ep          = "EP - Customer-Facing Apps"
      description = "Checkout flow, cart, order placement"
      runbook_url = "${var.runbook_base_url}/app/checkout"
    },
    {
      name        = "App - Orders API Team"
      team        = "App"
      ep          = "EP - Customer-Facing Apps"
      description = "Orders API, order management, fulfillment"
      runbook_url = "${var.runbook_base_url}/app/orders-api"
    },
    {
      name        = "App - Identity Team"
      team        = "App"
      ep          = "EP - Customer-Facing Apps"
      description = "Authentication, authorization, user management"
      runbook_url = "${var.runbook_base_url}/app/identity"
    },
    {
      name        = "Platform - Networking"
      team        = "Platform"
      ep          = "EP - Platform Core"
      description = "Network infrastructure, DNS, load balancers, CDN"
      runbook_url = "${var.runbook_base_url}/platform/networking"
    },
    {
      name        = "Platform - Kubernetes/Platform"
      team        = "Platform"
      ep          = "EP - Platform Core"
      description = "Kubernetes clusters, container orchestration"
      runbook_url = "${var.runbook_base_url}/platform/kubernetes"
    },
    {
      name        = "App - Backend API"
      team        = "App"
      ep          = "EP - Customer-Facing Apps"
      description = "Backend API services, REST/GraphQL endpoints"
      runbook_url = "${var.runbook_base_url}/app/backend-api"
    },
    {
      name        = "Platform - Frontend"
      team        = "App"
      ep          = "EP - Customer-Facing Apps"
      description = "Frontend applications, CDN, client-side monitoring"
      runbook_url = "${var.runbook_base_url}/platform/frontend"
    },
    {
      name        = "Platform - Network"
      team        = "Platform"
      ep          = "EP - Platform Core"
      description = "Core network infrastructure, routing, DNS"
      runbook_url = "${var.runbook_base_url}/platform/network"
    },
    {
      name        = "Database - DBRE Team"
      team        = "Platform"
      ep          = "EP - Data Services"
      description = "Database reliability engineering team operations"
      runbook_url = "${var.runbook_base_url}/data/dbre-team"
    },
    {
      name        = "DevOps - CI/CD Platform"
      team        = "Platform"
      ep          = "EP - Platform Core"
      description = "CI/CD pipelines, build systems, deployment automation"
      runbook_url = "${var.runbook_base_url}/devops/cicd"
    },
    {
      name        = "Payment Processing - Gateway"
      team        = "Support"
      ep          = "EP - Business Ops - Manual Operation"
      description = "Payment gateway processing, transaction handling"
      runbook_url = "${var.runbook_base_url}/payments/gateway"
    },
    {
      name        = "OT Operations - Factory Floor"
      team        = "Support"
      ep          = "EP - Business Ops - Manual Operation"
      description = "Operational technology, factory floor SCADA/IoT systems"
      runbook_url = "${var.runbook_base_url}/industry/factory-floor"
    },
    {
      name        = "Clinical Systems - EMR"
      team        = "Support"
      ep          = "EP - Business Ops - Manual Operation"
      description = "Electronic medical records, clinical systems"
      runbook_url = "${var.runbook_base_url}/industry/clinical-emr"
    },
    {
      name        = "Grid Operations Center"
      team        = "Support"
      ep          = "EP - Business Ops - Manual Operation"
      description = "Energy grid operations, SCADA, power management"
      runbook_url = "${var.runbook_base_url}/industry/grid-ops"
    },
    {
      name        = "Network Operations - Core"
      team        = "Platform"
      ep          = "EP - Platform Core"
      description = "Telecom/ISP core network operations"
      runbook_url = "${var.runbook_base_url}/industry/network-ops"
    },
    {
      name        = "Mining Operations - Equipment"
      team        = "Support"
      ep          = "EP - Business Ops - Manual Operation"
      description = "Mining equipment monitoring and operations"
      runbook_url = "${var.runbook_base_url}/industry/mining-equipment"
    },
    {
      name        = "Quality Control - Manufacturing"
      team        = "Support"
      ep          = "EP - Business Ops - Manual Operation"
      description = "Manufacturing quality control, defect detection"
      runbook_url = "${var.runbook_base_url}/industry/quality-control"
    },
    {
      name        = "Retail Systems - POS"
      team        = "Support"
      ep          = "EP - Business Ops - Manual Operation"
      description = "Point of sale systems, retail operations"
      runbook_url = "${var.runbook_base_url}/industry/retail-pos"
    },
    {
      name        = "Safety Operations"
      team        = "Support"
      ep          = "EP - Business Ops - Manual Operation"
      description = "Safety monitoring, environmental compliance"
      runbook_url = "${var.runbook_base_url}/industry/safety-ops"
    }
  ]
}
