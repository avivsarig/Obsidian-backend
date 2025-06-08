variable "environment" {
  description = "Environment name"
  type        = string
}

variable "project_name" {
  description = "Project name for resource naming"
  type        = string
}

variable "instance_type" {
  description = "EC2 instance type"
  type        = string
  default     = "t3.micro"
}

variable "vpc_id" {
  description = "VPC ID where instance will be created"
  type        = string
}

variable "subnet_id" {
  description = "Subnet ID for the instance"
  type        = string
}

variable "security_group_ids" {
  description = "List of security group IDs"
  type        = list(string)
}

variable "key_name" {
  description = "EC2 Key Pair name for SSH access"
  type        = string
  default     = ""
}

variable "backend_repo_url" {
  description = "Git repository URL for the backend code"
  type        = string
}

variable "backend_branch" {
  description = "Git branch to deploy for backend"
  type        = string
  default     = "main"
}

variable "vault_repo_url" {
  description = "Git repository URL for the vault"
  type        = string
}

variable "vault_branch" {
  description = "Git branch to deploy for vault"
  type        = string
  default     = "main"
}

variable "auto_update_enabled" {
  description = "Enable automatic git pulls (dev only)"
  type        = bool
  default     = false
}

variable "vault_deploy_key_secret_name" {
  description = "Name of the secret containing the vault deploy key"
  type        = string
  default     = "obsidian-automation/vault-deploy-key"
}

variable "aws_region" {
  description = "AWS region for resource creation"
  type        = string
}
