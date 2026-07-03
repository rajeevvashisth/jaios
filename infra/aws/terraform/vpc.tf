module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "~> 5.8"

  name = "${var.project_name}-${var.environment}"
  cidr = var.vpc_cidr

  azs             = slice(data.aws_availability_zones.available.names, 0, 2)
  private_subnets = [cidrsubnet(var.vpc_cidr, 4, 0), cidrsubnet(var.vpc_cidr, 4, 1)]
  public_subnets  = [cidrsubnet(var.vpc_cidr, 4, 8), cidrsubnet(var.vpc_cidr, 4, 9)]

  # Single NAT gateway keeps this skeleton cheap to run; switch to one per
  # AZ (enable_nat_gateway + one_nat_gateway_per_az) for real HA.
  enable_nat_gateway   = true
  single_nat_gateway   = true
  enable_dns_hostnames = true

  tags = local.tags
}
