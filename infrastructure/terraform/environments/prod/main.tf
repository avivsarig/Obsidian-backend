terraform {
  backend "s3" {
    key = "environments/prod/terraform.tfstate"
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
