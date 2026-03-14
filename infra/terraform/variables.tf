variable "aws_region" {
  description = "AWS region to deploy into"
  type        = string
  default     = "us-east-1"
}

variable "domain_name" {
  description = "Root domain name, e.g. laundry.example.com"
  type        = string
}

variable "db_password" {
  description = "PostgreSQL master password"
  type        = string
  sensitive   = true
}

variable "openai_api_key" {
  description = "OpenAI API key for GPT-4o Vision"
  type        = string
  sensitive   = true
}

variable "jwt_secret" {
  description = "JWT signing secret (min 32 chars)"
  type        = string
  sensitive   = true
}

variable "app_name" {
  description = "Short identifier for all resources"
  type        = string
  default     = "laundry"
}

variable "environment" {
  description = "Deployment environment tag"
  type        = string
  default     = "production"
}
