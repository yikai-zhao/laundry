locals {
  frontends = {
    staff    = { bucket_suffix = "staff",    domain = "staff.${var.domain_name}" }
    customer = { bucket_suffix = "customer", domain = "sign.${var.domain_name}" }
    admin    = { bucket_suffix = "admin",    domain = "admin.${var.domain_name}" }
  }
}

# --- S3 buckets for frontend static files ---
resource "aws_s3_bucket" "frontend" {
  for_each = local.frontends
  bucket   = "${var.app_name}-frontend-${each.value.bucket_suffix}-${data.aws_caller_identity.current.account_id}"
}

resource "aws_s3_bucket_public_access_block" "frontend" {
  for_each                = local.frontends
  bucket                  = aws_s3_bucket.frontend[each.key].id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_cloudfront_origin_access_control" "frontend" {
  for_each                          = local.frontends
  name                              = "${var.app_name}-frontend-${each.key}-oac"
  origin_access_control_origin_type = "s3"
  signing_behavior                  = "always"
  signing_protocol                  = "sigv4"
}

resource "aws_cloudfront_distribution" "staff" {
  enabled             = true
  price_class         = "PriceClass_100"
  aliases             = ["staff.${var.domain_name}"]
  default_root_object = "index.html"

  origin {
    domain_name              = aws_s3_bucket.frontend["staff"].bucket_regional_domain_name
    origin_id                = "staff-s3"
    origin_access_control_id = aws_cloudfront_origin_access_control.frontend["staff"].id
  }

  default_cache_behavior {
    target_origin_id       = "staff-s3"
    viewer_protocol_policy = "redirect-to-https"
    allowed_methods        = ["GET", "HEAD"]
    cached_methods         = ["GET", "HEAD"]
    compress               = true
    cache_policy_id        = "658327ea-f89d-4fab-a63d-7e88639e58f6"
  }

  # SPA routing: serve index.html on 403/404
  custom_error_response {
    error_code         = 403
    response_code      = 200
    response_page_path = "/index.html"
  }
  custom_error_response {
    error_code         = 404
    response_code      = 200
    response_page_path = "/index.html"
  }

  viewer_certificate {
    acm_certificate_arn      = aws_acm_certificate_validation.main.certificate_arn
    ssl_support_method       = "sni-only"
    minimum_protocol_version = "TLSv1.2_2021"
  }

  restrictions {
    geo_restriction { restriction_type = "none" }
  }
}

resource "aws_cloudfront_distribution" "customer" {
  enabled             = true
  price_class         = "PriceClass_100"
  aliases             = ["sign.${var.domain_name}"]
  default_root_object = "index.html"

  origin {
    domain_name              = aws_s3_bucket.frontend["customer"].bucket_regional_domain_name
    origin_id                = "customer-s3"
    origin_access_control_id = aws_cloudfront_origin_access_control.frontend["customer"].id
  }

  default_cache_behavior {
    target_origin_id       = "customer-s3"
    viewer_protocol_policy = "redirect-to-https"
    allowed_methods        = ["GET", "HEAD"]
    cached_methods         = ["GET", "HEAD"]
    compress               = true
    cache_policy_id        = "658327ea-f89d-4fab-a63d-7e88639e58f6"
  }

  custom_error_response {
    error_code         = 403
    response_code      = 200
    response_page_path = "/index.html"
  }
  custom_error_response {
    error_code         = 404
    response_code      = 200
    response_page_path = "/index.html"
  }

  viewer_certificate {
    acm_certificate_arn      = aws_acm_certificate_validation.main.certificate_arn
    ssl_support_method       = "sni-only"
    minimum_protocol_version = "TLSv1.2_2021"
  }

  restrictions {
    geo_restriction { restriction_type = "none" }
  }
}

resource "aws_cloudfront_distribution" "admin" {
  enabled             = true
  price_class         = "PriceClass_100"
  aliases             = ["admin.${var.domain_name}"]
  default_root_object = "index.html"

  origin {
    domain_name              = aws_s3_bucket.frontend["admin"].bucket_regional_domain_name
    origin_id                = "admin-s3"
    origin_access_control_id = aws_cloudfront_origin_access_control.frontend["admin"].id
  }

  default_cache_behavior {
    target_origin_id       = "admin-s3"
    viewer_protocol_policy = "redirect-to-https"
    allowed_methods        = ["GET", "HEAD"]
    cached_methods         = ["GET", "HEAD"]
    compress               = true
    cache_policy_id        = "658327ea-f89d-4fab-a63d-7e88639e58f6"
  }

  custom_error_response {
    error_code         = 403
    response_code      = 200
    response_page_path = "/index.html"
  }
  custom_error_response {
    error_code         = 404
    response_code      = 200
    response_page_path = "/index.html"
  }

  viewer_certificate {
    acm_certificate_arn      = aws_acm_certificate_validation.main.certificate_arn
    ssl_support_method       = "sni-only"
    minimum_protocol_version = "TLSv1.2_2021"
  }

  restrictions {
    geo_restriction { restriction_type = "none" }
  }
}

# Bucket policies for CloudFront OAC
resource "aws_s3_bucket_policy" "frontend" {
  for_each = local.frontends
  bucket   = aws_s3_bucket.frontend[each.key].id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Sid    = "AllowCloudFrontOAC"
      Effect = "Allow"
      Principal = { Service = "cloudfront.amazonaws.com" }
      Action   = "s3:GetObject"
      Resource = "${aws_s3_bucket.frontend[each.key].arn}/*"
      Condition = {
        StringEquals = {
          "AWS:SourceArn" = each.key == "staff" ? aws_cloudfront_distribution.staff.arn : (
            each.key == "customer" ? aws_cloudfront_distribution.customer.arn : aws_cloudfront_distribution.admin.arn
          )
        }
      }
    }]
  })
}
