terraform {
  backend "s3" {
    bucket         = "obsidian-backend-tf-state"
    region         = "eu-west-1"
    dynamodb_table = "terraform-state-locks"
    encrypt        = true
  }
}
