output "api_url" {
  description = "Backend API base URL"
  value       = "https://api.${var.domain_name}"
}

output "staff_url" {
  description = "Staff app URL"
  value       = "https://staff.${var.domain_name}"
}

output "customer_sign_url" {
  description = "Customer sign URL"
  value       = "https://sign.${var.domain_name}"
}

output "admin_url" {
  description = "Admin dashboard URL"
  value       = "https://admin.${var.domain_name}"
}

output "ecr_repository_url" {
  description = "ECR repository URL for backend Docker image"
  value       = aws_ecr_repository.backend.repository_url
}

output "s3_photos_bucket" {
  description = "S3 bucket name for photo uploads"
  value       = aws_s3_bucket.photos.id
}

output "cloudfront_photos_url" {
  description = "CloudFront CDN URL for photos"
  value       = "https://${aws_cloudfront_distribution.photos.domain_name}"
}

output "cloudfront_staff_id" {
  value = aws_cloudfront_distribution.staff.id
}

output "cloudfront_customer_id" {
  value = aws_cloudfront_distribution.customer.id
}

output "cloudfront_admin_id" {
  value = aws_cloudfront_distribution.admin.id
}

output "s3_staff_bucket" {
  value = aws_s3_bucket.frontend["staff"].id
}

output "s3_customer_bucket" {
  value = aws_s3_bucket.frontend["customer"].id
}

output "s3_admin_bucket" {
  value = aws_s3_bucket.frontend["admin"].id
}

output "rds_endpoint" {
  description = "RDS PostgreSQL host (for reference)"
  value       = aws_db_instance.main.address
  sensitive   = true
}

output "route53_nameservers" {
  description = "Point your domain registrar NS records to these"
  value       = aws_route53_zone.main.name_servers
}

output "github_actions_access_key_id" {
  description = "AWS_ACCESS_KEY_ID for GitHub Actions secrets"
  value       = aws_iam_access_key.github_actions.id
}

output "github_actions_secret_access_key" {
  description = "AWS_SECRET_ACCESS_KEY for GitHub Actions secrets"
  value       = aws_iam_access_key.github_actions.secret
  sensitive   = true
}
