# Cognito Module - User Authentication

# Cognito User Pool
resource "aws_cognito_user_pool" "main" {
  name = "${var.project_name}-${var.environment}-users"

  # Username configuration
  username_attributes      = ["email"]
  auto_verified_attributes = ["email"]

  # Password policy
  password_policy {
    minimum_length    = 8
    require_lowercase = true
    require_uppercase = true
    require_numbers   = true
    require_symbols   = false
  }

  # MFA configuration
  mfa_configuration = "OPTIONAL"

  # Email configuration
  email_configuration {
    email_sending_account = "COGNITO_DEFAULT"
  }

  # Account recovery
  account_recovery_setting {
    recovery_mechanism {
      name     = "verified_email"
      priority = 1
    }
  }

  tags = {
    Name = "${var.project_name}-${var.environment}-user-pool"
  }
}

# User Pool Client (for React app)
resource "aws_cognito_user_pool_client" "app_client" {
  name         = "${var.project_name}-${var.environment}-app-client"
  user_pool_id = aws_cognito_user_pool.main.id

  # OAuth configuration
  generate_secret                      = false  # For SPA
  allowed_oauth_flows_user_pool_client = true
  allowed_oauth_flows                  = ["code", "implicit"]
  allowed_oauth_scopes                 = ["email", "openid", "profile"]
  
  # Callback URLs (update with actual Amplify URL)
  callback_urls = [
    "http://localhost:3000",
    "https://localhost:3000"
  ]
  
  logout_urls = [
    "http://localhost:3000",
    "https://localhost:3000"
  ]

  # Token validity
  id_token_validity      = 60  # 1 hour
  access_token_validity  = 60  # 1 hour
  refresh_token_validity = 30  # 30 days

  token_validity_units {
    id_token      = "minutes"
    access_token  = "minutes"
    refresh_token = "days"
  }

  # Explicit auth flows
  explicit_auth_flows = [
    "ALLOW_USER_SRP_AUTH",
    "ALLOW_REFRESH_TOKEN_AUTH",
    "ALLOW_USER_PASSWORD_AUTH"
  ]
}

# User Group - Admin
resource "aws_cognito_user_group" "admin" {
  name         = "admin"
  user_pool_id = aws_cognito_user_pool.main.id
  description  = "Administrators with document upload permissions"
  precedence   = 1
}

# User Group - Researcher
resource "aws_cognito_user_group" "researcher" {
  name         = "researcher"
  user_pool_id = aws_cognito_user_pool.main.id
  description  = "Researchers with chat access only"
  precedence   = 2
}
