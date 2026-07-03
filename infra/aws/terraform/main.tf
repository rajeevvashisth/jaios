terraform {
  required_version = ">= 1.6"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.6"
    }
  }

  # Uncomment and fill in before the first `terraform init` against a
  # shared (non-solo) environment — without a remote backend, state lives
  # only on whichever machine ran `apply`.
  # backend "s3" {
  #   bucket         = "jaios-terraform-state"
  #   key            = "jaios/terraform.tfstate"
  #   region         = "us-east-1"
  #   dynamodb_table = "jaios-terraform-locks"
  #   encrypt        = true
  # }
}

provider "aws" {
  region = var.aws_region
}

data "aws_availability_zones" "available" {
  state = "available"
}

locals {
  tags = {
    Project     = var.project_name
    Environment = var.environment
    ManagedBy   = "terraform"
  }
}
