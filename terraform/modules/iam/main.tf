# IAM Module - Users, Roles, and Policies

# EC2 Instance Role
resource "aws_iam_role" "ec2_role" {
  name = "${var.project_name}-${var.environment}-ec2-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ec2.amazonaws.com"
        }
      }
    ]
  })

  tags = {
    Name = "${var.project_name}-${var.environment}-ec2-role"
  }
}

# EC2 Instance Profile
resource "aws_iam_instance_profile" "ec2_profile" {
  name = "${var.project_name}-${var.environment}-ec2-profile"
  role = aws_iam_role.ec2_role.name
}

# Policy for EC2 to access S3
resource "aws_iam_role_policy" "ec2_s3_policy" {
  name = "${var.project_name}-${var.environment}-ec2-s3-policy"
  role = aws_iam_role.ec2_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:ListBucket",
          "s3:DeleteObject"
        ]
        Resource = [
          "arn:aws:s3:::${var.project_name}-*",
          "arn:aws:s3:::${var.project_name}-*/*"
        ]
      }
    ]
  })
}

# Policy for EC2 to access DynamoDB
resource "aws_iam_role_policy" "ec2_dynamodb_policy" {
  name = "${var.project_name}-${var.environment}-ec2-dynamodb-policy"
  role = aws_iam_role.ec2_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "dynamodb:GetItem",
          "dynamodb:PutItem",
          "dynamodb:Query",
          "dynamodb:UpdateItem",
          "dynamodb:Scan",
          "dynamodb:BatchGetItem",
          "dynamodb:BatchWriteItem"
        ]
        Resource = "arn:aws:dynamodb:*:*:table/${var.project_name}-*"
      }
    ]
  })
}

# Policy for EC2 to access Bedrock
resource "aws_iam_role_policy" "ec2_bedrock_policy" {
  name = "${var.project_name}-${var.environment}-ec2-bedrock-policy"
  role = aws_iam_role.ec2_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "bedrock:InvokeModel",
          "bedrock:InvokeModelWithResponseStream"
        ]
        Resource = [
          "arn:aws:bedrock:*::foundation-model/anthropic.claude-3-5-sonnet-20240620-v1:0",
          "arn:aws:bedrock:*::foundation-model/amazon.titan-embed-text-v2:0"
        ]
      }
    ]
  })
}

# Policy for EC2 to access Textract
resource "aws_iam_role_policy" "ec2_textract_policy" {
  name = "${var.project_name}-${var.environment}-ec2-textract-policy"
  role = aws_iam_role.ec2_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "textract:AnalyzeDocument",
          "textract:DetectDocumentText"
        ]
        Resource = "*"
      }
    ]
  })
}

# Policy for EC2 to access SQS
resource "aws_iam_role_policy" "ec2_sqs_policy" {
  name = "${var.project_name}-${var.environment}-ec2-sqs-policy"
  role = aws_iam_role.ec2_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "sqs:ReceiveMessage",
          "sqs:DeleteMessage",
          "sqs:SendMessage",
          "sqs:GetQueueAttributes"
        ]
        Resource = "arn:aws:sqs:*:*:${var.project_name}-*"
      }
    ]
  })
}

# IAM Users for Team Members
resource "aws_iam_user" "tech_lead" {
  name = "${var.project_name}-tech-lead"
  
  tags = {
    Role = "Tech Lead"
  }
}

resource "aws_iam_user" "backend_idp" {
  name = "${var.project_name}-backend-idp"
  
  tags = {
    Role = "Backend+IDP Engineer"
  }
}

resource "aws_iam_user" "frontend" {
  name = "${var.project_name}-frontend"
  
  tags = {
    Role = "Frontend Engineer"
  }
}

resource "aws_iam_user" "devops" {
  name = "${var.project_name}-devops"
  
  tags = {
    Role = "DevOps Engineer"
  }
}

# Access Keys (output to console, not stored in state)
resource "aws_iam_access_key" "tech_lead_key" {
  user = aws_iam_user.tech_lead.name
}

resource "aws_iam_access_key" "backend_idp_key" {
  user = aws_iam_user.backend_idp.name
}

resource "aws_iam_access_key" "frontend_key" {
  user = aws_iam_user.frontend.name
}

resource "aws_iam_access_key" "devops_key" {
  user = aws_iam_user.devops.name
}

# Policy for Tech Lead (Full Access)
resource "aws_iam_user_policy" "tech_lead_policy" {
  name = "${var.project_name}-tech-lead-policy"
  user = aws_iam_user.tech_lead.name

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "ec2:*",
          "s3:*",
          "dynamodb:*",
          "bedrock:*",
          "textract:*",
          "sqs:*",
          "cloudwatch:*"
        ]
        Resource = "*"
      }
    ]
  })
}

# Policy for Backend+IDP Engineer
resource "aws_iam_user_policy" "backend_idp_policy" {
  name = "${var.project_name}-backend-idp-policy"
  user = aws_iam_user.backend_idp.name

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "ec2:Describe*",
          "s3:*",
          "dynamodb:*",
          "bedrock:InvokeModel",
          "textract:*",
          "sqs:*"
        ]
        Resource = "*"
      }
    ]
  })
}

# Policy for Frontend Engineer
resource "aws_iam_user_policy" "frontend_policy" {
  name = "${var.project_name}-frontend-policy"
  user = aws_iam_user.frontend.name

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "amplify:*",
          "cognito-idp:*",
          "s3:GetObject",
          "s3:ListBucket"
        ]
        Resource = "*"
      }
    ]
  })
}

# Policy for DevOps Engineer (Admin Access)
resource "aws_iam_user_policy_attachment" "devops_admin" {
  user       = aws_iam_user.devops.name
  policy_arn = "arn:aws:iam::aws:policy/AdministratorAccess"
}
