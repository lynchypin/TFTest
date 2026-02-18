# Business Services and Dependencies (provider v3.x syntax for service_dependency)

# =========================
# Data lookups: Technical Services (canonical names confirmed)
# =========================
data "pagerduty_service" "platform_k8s" { name = "Platform - Kubernetes/Platform" }
data "pagerduty_service" "platform_net" { name = "Platform - Networking" }
data "pagerduty_service" "platform_dbre" { name = "Platform - DBRE" }
data "pagerduty_service" "data_stream" { name = "Data - Streaming" }
data "pagerduty_service" "data_analytics" { name = "Data - Analytics" }
data "pagerduty_service" "secops" { name = "SecOps" }
data "pagerduty_service" "corp_it" { name = "Corp IT" }
data "pagerduty_service" "support" { name = "Support" }
data "pagerduty_service" "payments_ops" { name = "Payments Ops" }
data "pagerduty_service" "app_checkout" { name = "App - Checkout Team" }
data "pagerduty_service" "app_orders" { name = "App - Orders API Team" }
# app_identity: use managed resource reference instead of data source

# Optional: team lookup for stakeholder subscriptions
data "pagerduty_team" "support_team" { name = "Support" }

# =========================
# Business Services (names as requested)
# =========================
resource "pagerduty_business_service" "bs_checkout" { name = "Checkout" }
resource "pagerduty_business_service" "bs_orders" { name = "Orders" }
resource "pagerduty_business_service" "bs_identity" { name = "Identity" }
resource "pagerduty_business_service" "bs_customer_web" { name = "Customer Web" }
resource "pagerduty_business_service" "bs_mobile" { name = "Mobile" }
resource "pagerduty_business_service" "bs_payments" { name = "Payments" }
resource "pagerduty_business_service" "bs_analytics" { name = "Analytics" }
resource "pagerduty_business_service" "bs_support_portal" { name = "Support Portal" }
resource "pagerduty_business_service" "bs_business_ops" { name = "Business Ops" }

# =========================
# Locals: Define edges as maps to drive for_each
# =========================

# Business -> Technical edges
locals {
  bs_to_ts = {
    # Checkout
    "Checkout->App - Checkout Team" = {
      dependent_id    = pagerduty_business_service.bs_checkout.id
      dependent_type  = "business_service"
      supporting_id   = data.pagerduty_service.app_checkout.id
      supporting_type = "service"
    }
    "Checkout->App - Orders API Team" = {
      dependent_id    = pagerduty_business_service.bs_checkout.id
      dependent_type  = "business_service"
      supporting_id   = data.pagerduty_service.app_orders.id
      supporting_type = "service"
    }
    "Checkout->App - Identity Team" = {
      dependent_id    = pagerduty_business_service.bs_checkout.id
      dependent_type  = "business_service"
      supporting_id   = pagerduty_service.services["App - Identity Team"].id
      supporting_type = "service"
    }
    "Checkout->Payments Ops" = {
      dependent_id    = pagerduty_business_service.bs_checkout.id
      dependent_type  = "business_service"
      supporting_id   = data.pagerduty_service.payments_ops.id
      supporting_type = "service"
    }
    "Checkout->Platform - DBRE" = {
      dependent_id    = pagerduty_business_service.bs_checkout.id
      dependent_type  = "business_service"
      supporting_id   = data.pagerduty_service.platform_dbre.id
      supporting_type = "service"
    }
    "Checkout->Platform - Networking" = {
      dependent_id    = pagerduty_business_service.bs_checkout.id
      dependent_type  = "business_service"
      supporting_id   = data.pagerduty_service.platform_net.id
      supporting_type = "service"
    }
    "Checkout->Platform - Kubernetes/Platform" = {
      dependent_id    = pagerduty_business_service.bs_checkout.id
      dependent_type  = "business_service"
      supporting_id   = data.pagerduty_service.platform_k8s.id
      supporting_type = "service"
    }

    # Orders
    "Orders->App - Orders API Team" = {
      dependent_id    = pagerduty_business_service.bs_orders.id
      dependent_type  = "business_service"
      supporting_id   = data.pagerduty_service.app_orders.id
      supporting_type = "service"
    }
    "Orders->Platform - DBRE" = {
      dependent_id    = pagerduty_business_service.bs_orders.id
      dependent_type  = "business_service"
      supporting_id   = data.pagerduty_service.platform_dbre.id
      supporting_type = "service"
    }
    "Orders->Platform - Networking" = {
      dependent_id    = pagerduty_business_service.bs_orders.id
      dependent_type  = "business_service"
      supporting_id   = data.pagerduty_service.platform_net.id
      supporting_type = "service"
    }
    "Orders->Platform - Kubernetes/Platform" = {
      dependent_id    = pagerduty_business_service.bs_orders.id
      dependent_type  = "business_service"
      supporting_id   = data.pagerduty_service.platform_k8s.id
      supporting_type = "service"
    }

    # Identity
    "Identity->App - Identity Team" = {
      dependent_id    = pagerduty_business_service.bs_identity.id
      dependent_type  = "business_service"
      supporting_id   = pagerduty_service.services["App - Identity Team"].id
      supporting_type = "service"
    }
    "Identity->Platform - DBRE" = {
      dependent_id    = pagerduty_business_service.bs_identity.id
      dependent_type  = "business_service"
      supporting_id   = data.pagerduty_service.platform_dbre.id
      supporting_type = "service"
    }
    "Identity->Platform - Networking" = {
      dependent_id    = pagerduty_business_service.bs_identity.id
      dependent_type  = "business_service"
      supporting_id   = data.pagerduty_service.platform_net.id
      supporting_type = "service"
    }
    "Identity->Platform - Kubernetes/Platform" = {
      dependent_id    = pagerduty_business_service.bs_identity.id
      dependent_type  = "business_service"
      supporting_id   = data.pagerduty_service.platform_k8s.id
      supporting_type = "service"
    }

    # Customer Web
    "Customer Web->App - Orders API Team" = {
      dependent_id    = pagerduty_business_service.bs_customer_web.id
      dependent_type  = "business_service"
      supporting_id   = data.pagerduty_service.app_orders.id
      supporting_type = "service"
    }
    "Customer Web->App - Identity Team" = {
      dependent_id    = pagerduty_business_service.bs_customer_web.id
      dependent_type  = "business_service"
      supporting_id   = pagerduty_service.services["App - Identity Team"].id
      supporting_type = "service"
    }
    "Customer Web->Platform - Networking" = {
      dependent_id    = pagerduty_business_service.bs_customer_web.id
      dependent_type  = "business_service"
      supporting_id   = data.pagerduty_service.platform_net.id
      supporting_type = "service"
    }
    "Customer Web->Platform - Kubernetes/Platform" = {
      dependent_id    = pagerduty_business_service.bs_customer_web.id
      dependent_type  = "business_service"
      supporting_id   = data.pagerduty_service.platform_k8s.id
      supporting_type = "service"
    }

    # Mobile
    "Mobile->App - Orders API Team" = {
      dependent_id    = pagerduty_business_service.bs_mobile.id
      dependent_type  = "business_service"
      supporting_id   = data.pagerduty_service.app_orders.id
      supporting_type = "service"
    }
    "Mobile->App - Identity Team" = {
      dependent_id    = pagerduty_business_service.bs_mobile.id
      dependent_type  = "business_service"
      supporting_id   = pagerduty_service.services["App - Identity Team"].id
      supporting_type = "service"
    }
    "Mobile->Platform - Networking" = {
      dependent_id    = pagerduty_business_service.bs_mobile.id
      dependent_type  = "business_service"
      supporting_id   = data.pagerduty_service.platform_net.id
      supporting_type = "service"
    }
    "Mobile->Platform - Kubernetes/Platform" = {
      dependent_id    = pagerduty_business_service.bs_mobile.id
      dependent_type  = "business_service"
      supporting_id   = data.pagerduty_service.platform_k8s.id
      supporting_type = "service"
    }

    # Payments
    "Payments->Payments Ops" = {
      dependent_id    = pagerduty_business_service.bs_payments.id
      dependent_type  = "business_service"
      supporting_id   = data.pagerduty_service.payments_ops.id
      supporting_type = "service"
    }
    "Payments->Platform - DBRE" = {
      dependent_id    = pagerduty_business_service.bs_payments.id
      dependent_type  = "business_service"
      supporting_id   = data.pagerduty_service.platform_dbre.id
      supporting_type = "service"
    }
    "Payments->Platform - Networking" = {
      dependent_id    = pagerduty_business_service.bs_payments.id
      dependent_type  = "business_service"
      supporting_id   = data.pagerduty_service.platform_net.id
      supporting_type = "service"
    }
    "Payments->Platform - Kubernetes/Platform" = {
      dependent_id    = pagerduty_business_service.bs_payments.id
      dependent_type  = "business_service"
      supporting_id   = data.pagerduty_service.platform_k8s.id
      supporting_type = "service"
    }
    "Payments->App - Checkout Team" = {
      dependent_id    = pagerduty_business_service.bs_payments.id
      dependent_type  = "business_service"
      supporting_id   = data.pagerduty_service.app_checkout.id
      supporting_type = "service"
    }

    # Analytics
    "Analytics->Data - Analytics" = {
      dependent_id    = pagerduty_business_service.bs_analytics.id
      dependent_type  = "business_service"
      supporting_id   = data.pagerduty_service.data_analytics.id
      supporting_type = "service"
    }
    "Analytics->Data - Streaming" = {
      dependent_id    = pagerduty_business_service.bs_analytics.id
      dependent_type  = "business_service"
      supporting_id   = data.pagerduty_service.data_stream.id
      supporting_type = "service"
    }
    "Analytics->Platform - DBRE" = {
      dependent_id    = pagerduty_business_service.bs_analytics.id
      dependent_type  = "business_service"
      supporting_id   = data.pagerduty_service.platform_dbre.id
      supporting_type = "service"
    }
    "Analytics->Platform - Kubernetes/Platform" = {
      dependent_id    = pagerduty_business_service.bs_analytics.id
      dependent_type  = "business_service"
      supporting_id   = data.pagerduty_service.platform_k8s.id
      supporting_type = "service"
    }
    "Analytics->Platform - Networking" = {
      dependent_id    = pagerduty_business_service.bs_analytics.id
      dependent_type  = "business_service"
      supporting_id   = data.pagerduty_service.platform_net.id
      supporting_type = "service"
    }

    # Support Portal
    "Support Portal->Support" = {
      dependent_id    = pagerduty_business_service.bs_support_portal.id
      dependent_type  = "business_service"
      supporting_id   = data.pagerduty_service.support.id
      supporting_type = "service"
    }
    "Support Portal->Corp IT" = {
      dependent_id    = pagerduty_business_service.bs_support_portal.id
      dependent_type  = "business_service"
      supporting_id   = data.pagerduty_service.corp_it.id
      supporting_type = "service"
    }
    "Support Portal->Platform - Networking" = {
      dependent_id    = pagerduty_business_service.bs_support_portal.id
      dependent_type  = "business_service"
      supporting_id   = data.pagerduty_service.platform_net.id
      supporting_type = "service"
    }

    # Business Ops
    "Business Ops->Corp IT" = {
      dependent_id    = pagerduty_business_service.bs_business_ops.id
      dependent_type  = "business_service"
      supporting_id   = data.pagerduty_service.corp_it.id
      supporting_type = "service"
    }
    "Business Ops->Support" = {
      dependent_id    = pagerduty_business_service.bs_business_ops.id
      dependent_type  = "business_service"
      supporting_id   = data.pagerduty_service.support.id
      supporting_type = "service"
    }
    "Business Ops->Platform - Networking" = {
      dependent_id    = pagerduty_business_service.bs_business_ops.id
      dependent_type  = "business_service"
      supporting_id   = data.pagerduty_service.platform_net.id
      supporting_type = "service"
    }
  }
}

# Business -> Business edges
locals {
  bs_to_bs = {
    "Checkout->Orders" = {
      dependent_id    = pagerduty_business_service.bs_checkout.id
      dependent_type  = "business_service"
      supporting_id   = pagerduty_business_service.bs_orders.id
      supporting_type = "business_service"
    }
    "Checkout->Identity" = {
      dependent_id    = pagerduty_business_service.bs_checkout.id
      dependent_type  = "business_service"
      supporting_id   = pagerduty_business_service.bs_identity.id
      supporting_type = "business_service"
    }
    "Checkout->Payments" = {
      dependent_id    = pagerduty_business_service.bs_checkout.id
      dependent_type  = "business_service"
      supporting_id   = pagerduty_business_service.bs_payments.id
      supporting_type = "business_service"
    }
    "Customer Web->Orders" = {
      dependent_id    = pagerduty_business_service.bs_customer_web.id
      dependent_type  = "business_service"
      supporting_id   = pagerduty_business_service.bs_orders.id
      supporting_type = "business_service"
    }
    "Customer Web->Identity" = {
      dependent_id    = pagerduty_business_service.bs_customer_web.id
      dependent_type  = "business_service"
      supporting_id   = pagerduty_business_service.bs_identity.id
      supporting_type = "business_service"
    }
    "Mobile->Identity" = {
      dependent_id    = pagerduty_business_service.bs_mobile.id
      dependent_type  = "business_service"
      supporting_id   = pagerduty_business_service.bs_identity.id
      supporting_type = "business_service"
    }
    "Mobile->Orders" = {
      dependent_id    = pagerduty_business_service.bs_mobile.id
      dependent_type  = "business_service"
      supporting_id   = pagerduty_business_service.bs_orders.id
      supporting_type = "business_service"
    }
    "Analytics->Orders" = {
      dependent_id    = pagerduty_business_service.bs_analytics.id
      dependent_type  = "business_service"
      supporting_id   = pagerduty_business_service.bs_orders.id
      supporting_type = "business_service"
    }
    "Business Ops->Support Portal" = {
      dependent_id    = pagerduty_business_service.bs_business_ops.id
      dependent_type  = "business_service"
      supporting_id   = pagerduty_business_service.bs_support_portal.id
      supporting_type = "business_service"
    }
  }
}

# =========================
# Resources: Edges
# =========================

# All Business -> Technical edges
resource "pagerduty_service_dependency" "bs_to_ts" {
  for_each = local.bs_to_ts

  dependency {
    dependent_service {
      id   = each.value.dependent_id
      type = each.value.dependent_type
    }
    supporting_service {
      id   = each.value.supporting_id
      type = each.value.supporting_type
    }
  }
}

# All Business -> Business edges
resource "pagerduty_service_dependency" "bs_to_bs" {
  for_each = local.bs_to_bs

  dependency {
    dependent_service {
      id   = each.value.dependent_id
      type = each.value.dependent_type
    }
    supporting_service {
      id   = each.value.supporting_id
      type = each.value.supporting_type
    }
  }
}

# =========================
# Stakeholder auto-subscriptions (two Business Services)
# If your provider version does not support this resource, remove these two blocks.
# =========================
resource "pagerduty_business_service_subscriber" "sub_checkout_support_team" {
  business_service_id = pagerduty_business_service.bs_checkout.id
  subscriber_id       = data.pagerduty_team.support_team.id
  subscriber_type     = "team"
}

resource "pagerduty_business_service_subscriber" "sub_customer_web_support_team" {
  business_service_id = pagerduty_business_service.bs_customer_web.id
  subscriber_id       = data.pagerduty_team.support_team.id
  subscriber_type     = "team"
}
