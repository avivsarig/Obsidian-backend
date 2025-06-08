terraform {
  backend "s3" {
    bucket         = "obsidian-backend-tf-state"
    key            = "environments/prod/terraform.tfstate"
    region         = "eu-west-1"
    dynamodb_table = "terraform-state-locks"
    encrypt        = true
  }
}

terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = var.project_name
      Environment = var.environment
      ManagedBy   = "opentofu"
    }
  }
}

resource "aws_iam_openid_connect_provider" "github_actions" {
  url = "https://token.actions.githubusercontent.com"

  thumbprint_list = ["6938fd4d98bab03faadb97b34396831e3780aea1"]

  client_id_list = ["sts.amazonaws.com"]

  tags = {
    Name = "${var.project_name}-github-oidc"
  }
}

resource "aws_iam_role" "github_actions" {
  name = "${var.project_name}-github-actions-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Federated = aws_iam_openid_connect_provider.github_actions.arn
        }
        Action = "sts:AssumeRoleWithWebIdentity"
        Condition = {
          StringEquals = {
            "token.actions.githubusercontent.com:sub" = "repo:avivsarig/Obsidian-backend:ref:refs/heads/main"
            "token.actions.githubusercontent.com:aud" = "sts.amazonaws.com"
          }
        }
      }
    ]
  })
}

resource "aws_iam_role_policy" "github_actions_terraform" {
  name = "${var.project_name}-github-actions-terraform"
  role = aws_iam_role.github_actions.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        # Terraform state S3 access
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject"
        ]
        Resource = [
          "arn:aws:s3:::obsidian-backend-tf-state/environments/prod/*"
        ]
      },
      {
        # S3 bucket listing for state file
        Effect = "Allow"
        Action = [
          "s3:ListBucket"
        ]
        Resource = "arn:aws:s3:::obsidian-backend-tf-state"
      },
      {
        # DynamoDB state locking
        Effect = "Allow"
        Action = [
          "dynamodb:GetItem",
          "dynamodb:PutItem",
          "dynamodb:DeleteItem"
        ]
        Resource = "arn:aws:dynamodb:${var.aws_region}:*:table/terraform-state-locks"
      },
      {
        # EC2 read permissions for getting instance info
        Effect = "Allow"
        Action = [
          "ec2:DescribeInstances",
          "ec2:DescribeImages",
          "ec2:DescribeKeyPairs",
          "ec2:DescribeSecurityGroups",
          "ec2:DescribeSubnets",
          "ec2:DescribeVpcs"
        ]
        Resource = "*"
      },
      {
        # Systems Manager permissions for deployment
        Effect = "Allow"
        Action = [
          "ssm:SendCommand",
          "ssm:GetCommandInvocation",
          "ssm:DescribeInstanceInformation"
        ]
        Resource = [
          "arn:aws:ec2:${var.aws_region}:*:instance/*",
          "arn:aws:ssm:${var.aws_region}:*:document/AWS-RunShellScript",
          "arn:aws:ssm:${var.aws_region}:*:*"
        ]
      }
    ]
  })
}

module "networking" {
  source = "../../modules/networking"

  environment        = var.environment
  project_name       = var.project_name
  vpc_cidr           = "10.1.0.0/16"
  availability_zone  = var.availability_zone
  public_subnet_cidr = "10.1.1.0/24"
}

module "compute" {
  source = "../../modules/compute"

  environment        = var.environment
  project_name       = var.project_name
  instance_type      = var.instance_type
  vpc_id             = module.networking.vpc_id
  subnet_id          = module.networking.public_subnet_id
  security_group_ids = [module.networking.web_security_group_id]

  backend_repo_url    = var.backend_repo_url
  backend_branch      = "main"
  vault_repo_url      = var.vault_repo_url
  vault_branch        = "main"
  auto_update_enabled = false

  aws_region                   = var.aws_region
  vault_deploy_key_secret_name = "obsidian-automation/vault-deploy-key"
}
