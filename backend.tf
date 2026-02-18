# Terraform Remote State Configuration
# Choose ONE of the options below

# =============================================================================
# OPTION 1: Terraform Cloud (Recommended - Free tier available)
# =============================================================================
# 1. Sign up at https://app.terraform.io/
# 2. Create organization and workspace
# 3. Uncomment and configure below:

# terraform {
#   cloud {
#     organization = "your-org-name"
#     workspaces {
#       name = "pagerduty-demo"
#     }
#   }
# }

# =============================================================================
# OPTION 2: AWS S3 Backend (requires AWS account)
# =============================================================================
# 1. Create S3 bucket and DynamoDB table (use bootstrap script below)
# 2. Uncomment and configure:

# terraform {
#   backend "s3" {
#     bucket         = "your-terraform-state-bucket"
#     key            = "pagerduty-demo/terraform.tfstate"
#     region         = "us-east-1"
#     encrypt        = true
#     dynamodb_table = "terraform-state-lock"
#   }
# }

# =============================================================================
# OPTION 3: GitLab CI/CD State (if using GitLab)
# =============================================================================
# terraform {
#   backend "http" {
#     address        = "https://gitlab.com/api/v4/projects/<PROJECT_ID>/terraform/state/pagerduty"
#     lock_address   = "https://gitlab.com/api/v4/projects/<PROJECT_ID>/terraform/state/pagerduty/lock"
#     unlock_address = "https://gitlab.com/api/v4/projects/<PROJECT_ID>/terraform/state/pagerduty/lock"
#     username       = "your-username"
#     password       = "your-access-token"
#     lock_method    = "POST"
#     unlock_method  = "DELETE"
#     retry_wait_min = 5
#   }
# }
