resource "aws_security_group" "web" {
  name_prefix = "${var.project_name}-${var.environment}-web-"
  vpc_id      = aws_vpc.main.id
  description = "Security group for web/API servers"

  tags = {
    Name = "${var.project_name}-${var.environment}-web-sg"
  }
}

resource "aws_vpc_security_group_ingress_rule" "web_http" {
  security_group_id = aws_security_group.web.id
  description       = "HTTP"
  from_port         = 80
  to_port           = 80
  ip_protocol       = "tcp"
  cidr_ipv4         = "0.0.0.0/0"
}

resource "aws_vpc_security_group_ingress_rule" "web_https" {
  security_group_id = aws_security_group.web.id
  description       = "HTTPS"
  from_port         = 443
  to_port           = 443
  ip_protocol       = "tcp"
  cidr_ipv4         = "0.0.0.0/0"
}

# Add this data source
data "http" "my_ip" {
  url = "http://ipv4.icanhazip.com"
}

resource "aws_vpc_security_group_ingress_rule" "web_ssh" {
  cidr_ipv4         = "${chomp(data.http.my_ip.response_body)}/32"
  description       = "SSH"
  from_port         = 22
  security_group_id = aws_security_group.web.id
  to_port           = 22
  ip_protocol       = "tcp"
}

resource "aws_vpc_security_group_egress_rule" "web_all_outbound" {
  security_group_id = aws_security_group.web.id
  description       = "All outbound traffic"
  ip_protocol       = "-1"
  cidr_ipv4         = "0.0.0.0/0"
}
