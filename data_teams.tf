// Look up existing teams by name
data "pagerduty_team" "team_app" {
  name = "App"
}

data "pagerduty_team" "team_platform" {
  name = "Platform"
}

data "pagerduty_team" "team_support" {
  name = "Support"
}

data "pagerduty_team" "team_secops" {
  name = "SecOps"
}

data "pagerduty_team" "team_corp_it" {
  name = "Corp IT"
}
