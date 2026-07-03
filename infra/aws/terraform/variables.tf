variable "aws_region" {
  description = "AWS region to deploy into."
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Short name used to prefix/tag every resource."
  type        = string
  default     = "jaios"
}

variable "environment" {
  description = "Deployment environment name (e.g. staging, production)."
  type        = string
  default     = "production"
}

variable "vpc_cidr" {
  type    = string
  default = "10.42.0.0/16"
}

variable "db_instance_class" {
  type    = string
  default = "db.t4g.micro"
}

variable "db_allocated_storage_gb" {
  type    = number
  default = 20
}

variable "db_name" {
  type    = string
  default = "jaios"
}

variable "db_username" {
  type    = string
  default = "jaios"
}

variable "backend_image_tag" {
  description = "Tag of the backend image in ECR to deploy."
  type        = string
  default     = "latest"
}

variable "frontend_image_tag" {
  description = "Tag of the frontend image in ECR to deploy."
  type        = string
  default     = "latest"
}

variable "backend_cpu" {
  type    = number
  default = 512
}

variable "backend_memory" {
  type    = number
  default = 1024
}

variable "frontend_cpu" {
  type    = number
  default = 256
}

variable "frontend_memory" {
  type    = number
  default = 512
}

variable "backend_desired_count" {
  type    = number
  default = 1
}

variable "frontend_desired_count" {
  type    = number
  default = 1
}

variable "anthropic_api_key" {
  description = "Set via -var or TF_VAR_anthropic_api_key. Stored only in Secrets Manager — never printed as a Terraform output."
  type        = string
  sensitive   = true
  default     = ""
}

variable "jwt_secret_key" {
  description = "Set via -var or TF_VAR_jwt_secret_key, e.g. `openssl rand -hex 32`. No default — Terraform will prompt or fail rather than silently deploy the insecure app default."
  type        = string
  sensitive   = true
}
