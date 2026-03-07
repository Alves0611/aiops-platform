terraform {
  backend "s3" {
    bucket       = "tfstate-444065722670"
    key          = "networking/terraform.tfstate"
    region       = "us-east-1"
    use_lockfile = true
  }

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
  }
}