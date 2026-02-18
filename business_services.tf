resource "pagerduty_business_service" "ecommerce_platform" {
  name             = "E-Commerce Platform"
  description      = "Customer-facing e-commerce platform - revenue generating"
  point_of_contact = "platform-team@company.com"
  team             = pagerduty_team.platform.id
}

resource "pagerduty_business_service" "payment_processing" {
  name             = "Payment Processing"
  description      = "Payment gateway and transaction processing - direct revenue impact"
  point_of_contact = "payments-team@company.com"
  team             = pagerduty_team.platform.id
}

resource "pagerduty_business_service" "customer_identity" {
  name             = "Customer Identity"
  description      = "Authentication, authorization, and customer account management"
  point_of_contact = "identity-team@company.com"
  team             = pagerduty_team.platform.id
}

resource "pagerduty_business_service" "order_fulfillment" {
  name             = "Order Fulfillment"
  description      = "Order processing, inventory, and fulfillment operations"
  point_of_contact = "orders-team@company.com"
  team             = pagerduty_team.platform.id
}

resource "pagerduty_business_service" "data_analytics" {
  name             = "Data & Analytics"
  description      = "Business intelligence, reporting, and data pipelines"
  point_of_contact = "data-team@company.com"
  team             = pagerduty_team.platform.id
}

resource "pagerduty_business_service" "internal_tools" {
  name             = "Internal Tools"
  description      = "Internal employee tools and administrative systems"
  point_of_contact = "internal-tools@company.com"
  team             = pagerduty_team.platform.id
}

resource "pagerduty_service_dependency" "ecommerce_checkout" {
  dependency {
    dependent_service {
      id   = pagerduty_business_service.ecommerce_platform.id
      type = "business_service"
    }
    supporting_service {
      id   = pagerduty_service.svc_checkout_orch.id
      type = "service"
    }
  }
}

resource "pagerduty_service_dependency" "ecommerce_orders" {
  dependency {
    dependent_service {
      id   = pagerduty_business_service.ecommerce_platform.id
      type = "business_service"
    }
    supporting_service {
      id   = pagerduty_service.svc_orders_orch.id
      type = "service"
    }
  }
}

resource "pagerduty_service_dependency" "ecommerce_identity" {
  dependency {
    dependent_service {
      id   = pagerduty_business_service.ecommerce_platform.id
      type = "business_service"
    }
    supporting_service {
      id   = pagerduty_service.svc_identity_orch.id
      type = "service"
    }
  }
}

resource "pagerduty_service_dependency" "payment_payments" {
  dependency {
    dependent_service {
      id   = pagerduty_business_service.payment_processing.id
      type = "business_service"
    }
    supporting_service {
      id   = pagerduty_service.svc_payments_orch.id
      type = "service"
    }
  }
}

resource "pagerduty_service_dependency" "identity_identity" {
  dependency {
    dependent_service {
      id   = pagerduty_business_service.customer_identity.id
      type = "business_service"
    }
    supporting_service {
      id   = pagerduty_service.svc_identity_orch.id
      type = "service"
    }
  }
}

resource "pagerduty_service_dependency" "fulfillment_orders" {
  dependency {
    dependent_service {
      id   = pagerduty_business_service.order_fulfillment.id
      type = "business_service"
    }
    supporting_service {
      id   = pagerduty_service.svc_orders_orch.id
      type = "service"
    }
  }
}

resource "pagerduty_service_dependency" "analytics_streaming" {
  dependency {
    dependent_service {
      id   = pagerduty_business_service.data_analytics.id
      type = "business_service"
    }
    supporting_service {
      id   = pagerduty_service.svc_streaming_orch.id
      type = "service"
    }
  }
}

resource "pagerduty_service_dependency" "analytics_analytics" {
  dependency {
    dependent_service {
      id   = pagerduty_business_service.data_analytics.id
      type = "business_service"
    }
    supporting_service {
      id   = pagerduty_service.svc_analytics_orch.id
      type = "service"
    }
  }
}

resource "pagerduty_service_dependency" "checkout_depends_payments" {
  dependency {
    dependent_service {
      id   = pagerduty_service.svc_checkout_orch.id
      type = "service"
    }
    supporting_service {
      id   = pagerduty_service.svc_payments_orch.id
      type = "service"
    }
  }
}

resource "pagerduty_service_dependency" "checkout_depends_identity" {
  dependency {
    dependent_service {
      id   = pagerduty_service.svc_checkout_orch.id
      type = "service"
    }
    supporting_service {
      id   = pagerduty_service.svc_identity_orch.id
      type = "service"
    }
  }
}

resource "pagerduty_service_dependency" "orders_depends_payments" {
  dependency {
    dependent_service {
      id   = pagerduty_service.svc_orders_orch.id
      type = "service"
    }
    supporting_service {
      id   = pagerduty_service.svc_payments_orch.id
      type = "service"
    }
  }
}

resource "pagerduty_service_dependency" "payments_depends_database" {
  dependency {
    dependent_service {
      id   = pagerduty_service.svc_payments_orch.id
      type = "service"
    }
    supporting_service {
      id   = pagerduty_service.svc_dbre.id
      type = "service"
    }
  }
}

resource "pagerduty_service_dependency" "orders_depends_database" {
  dependency {
    dependent_service {
      id   = pagerduty_service.svc_orders_orch.id
      type = "service"
    }
    supporting_service {
      id   = pagerduty_service.svc_dbre.id
      type = "service"
    }
  }
}

resource "pagerduty_service_dependency" "identity_depends_database" {
  dependency {
    dependent_service {
      id   = pagerduty_service.svc_identity_orch.id
      type = "service"
    }
    supporting_service {
      id   = pagerduty_service.svc_dbre.id
      type = "service"
    }
  }
}

resource "pagerduty_service_dependency" "streaming_depends_k8s" {
  dependency {
    dependent_service {
      id   = pagerduty_service.svc_streaming_orch.id
      type = "service"
    }
    supporting_service {
      id   = pagerduty_service.svc_k8s.id
      type = "service"
    }
  }
}

resource "pagerduty_service_dependency" "analytics_depends_k8s" {
  dependency {
    dependent_service {
      id   = pagerduty_service.svc_analytics_orch.id
      type = "service"
    }
    supporting_service {
      id   = pagerduty_service.svc_k8s.id
      type = "service"
    }
  }
}
