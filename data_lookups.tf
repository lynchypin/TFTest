locals {
  team_names = toset(["Platform", "App", "Support", "Corp IT", "SecOps"])
}

data "pagerduty_team" "by_name" {
  for_each = local.team_names
  name     = each.key
}

locals {
  emails = {
    "jbeam@losandesgaa.onmicrosoft.com"    = "Jim Beam"
    "jcasker@losandesgaa.onmicrosoft.com"  = "Jameson Casker"
    "aguiness@losandesgaa.onmicrosoft.com" = "Arthur Guinness"
    "jcuervo@losandesgaa.onmicrosoft.com"  = "Jose Cuervo"
    "jdaniels@losandesgaa.onmicrosoft.com" = "Jack Daniels"
    "gtonic@losandesgaa.onmicrosoft.com"   = "Ginny Tonic"
  }
}

data "pagerduty_user" "by_email" {
  for_each = toset(keys(local.emails))
  email    = each.key
}
