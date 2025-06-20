output "ssh_connection" {
  value       = module.compute.ssh_connection_command
  description = "SSH command to connect to the instance"
}

output "instance_public_ip" {
  value       = module.compute.public_ip
  description = "Public IP of the instance"
}

output "instance_id" {
  value       = module.compute.instance_id
  description = "Instance ID"
}

output "github_actions_role_arn" {
  description = "ARN of the role for GitHub Actions to assume"
  value       = aws_iam_role.github_actions.arn
}

output "export_ip_command" {
  value       = "export OBSIDIAN_API_IP=${module.compute.public_ip}"
  description = "Command to set SERVER_IP environment variable"
}

output "health_check_command" {
  value       = "curl http://$OBSIDIAN_API_IP/api/v1/health"
  description = "Command to test the deployment"
}
