data "aws_ami" "ubuntu" {
  most_recent = true
  owners      = ["099720109477"] # Canonical

  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

resource "aws_key_pair" "main" {
  key_name   = "${var.project_name}-${var.environment}-key"
  public_key = file("~/.ssh/id_rsa.pub")

  tags = {
    Name        = "${var.project_name}-${var.environment}-key"
    Environment = var.environment
    Project     = var.project_name
  }
}

resource "aws_instance" "web" {
  ami                    = data.aws_ami.ubuntu.id
  instance_type          = var.instance_type
  subnet_id              = var.subnet_id
  vpc_security_group_ids = var.security_group_ids
  key_name               = aws_key_pair.main.key_name
  iam_instance_profile   = aws_iam_instance_profile.web.name
  ebs_optimized          = true
  monitoring             = false

  metadata_options {
    http_endpoint               = "enabled"
    http_tokens                 = "required" # Force IMDSv2
    http_put_response_hop_limit = 1
  }

  user_data = base64encode(templatefile("${path.module}/cloud-init.yml", {
    project_name                 = var.project_name
    environment                  = var.environment
    backend_repo_url             = var.backend_repo_url
    backend_branch               = var.backend_branch
    vault_repo_url               = var.vault_repo_url
    vault_branch                 = var.vault_branch
    auto_update_enabled          = var.auto_update_enabled
    vault_deploy_key_secret_name = var.vault_deploy_key_secret_name
    aws_region                   = var.aws_region
  }))

  root_block_device {
    volume_type = "gp3"
    volume_size = 8
    encrypted   = true
  }

  tags = {
    Name = "${var.project_name}-${var.environment}-web"
    Type = "WebServer"
  }
}

resource "aws_iam_role" "web" {
  name = "${var.project_name}-${var.environment}-web-role"

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
}

resource "aws_iam_role_policy" "parameter_store" {
  name = "${var.project_name}-${var.environment}-parameter-store"
  role = aws_iam_role.web.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "ssm:GetParameter",
          "ssm:GetParameters",
          "ssm:GetParametersByPath"
        ]
        Resource = "arn:aws:ssm:*:*:parameter/${var.project_name}/${var.environment}/*"
      }
    ]
  })
}

resource "aws_iam_role_policy" "secrets_access" {
  name = "${var.project_name}-${var.environment}-secrets-access"
  role = aws_iam_role.web.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "secretsmanager:GetSecretValue"
        ]
        Resource = [
          # Using a pattern that matches your secret naming convention
          "arn:aws:secretsmanager:${var.aws_region}:*:secret:${var.vault_deploy_key_secret_name}-*"
        ]
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "web_ssm" {
  role       = aws_iam_role.web.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
}

resource "aws_iam_instance_profile" "web" {
  name = "${var.project_name}-${var.environment}-web-profile"
  role = aws_iam_role.web.name
}
