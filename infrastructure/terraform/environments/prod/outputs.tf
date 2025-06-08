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
