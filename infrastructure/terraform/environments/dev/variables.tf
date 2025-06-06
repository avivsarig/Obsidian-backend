variable "environment" {
  description = "Environment name"
  type        = string
}

variable "aws_region" {
  description = "AWS region"
  type        = string
}

variable "project_name" {
  description = "Project name"
  type        = string
}

variable "instance_type" {
  description = "EC2 instance type"
  type        = string
}

variable "availability_zone" {
  description = "Availability zone"
  type        = string
}

variable "backend_repo_url" {
  description = "Backend repository URL"
  type        = string
}

variable "vault_repo_url" {
  description = "Vault repository URL"
  type        = string
}
