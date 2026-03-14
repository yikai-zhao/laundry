resource "aws_route53_zone" "main" {
  name = var.domain_name
}

# API backend — points to ALB
resource "aws_route53_record" "api" {
  zone_id = aws_route53_zone.main.zone_id
  name    = "api.${var.domain_name}"
  type    = "A"
  alias {
    name                   = aws_lb.main.dns_name
    zone_id                = aws_lb.main.zone_id
    evaluate_target_health = true
  }
}

# Staff app frontend
resource "aws_route53_record" "staff" {
  zone_id = aws_route53_zone.main.zone_id
  name    = "staff.${var.domain_name}"
  type    = "A"
  alias {
    name                   = aws_cloudfront_distribution.staff.domain_name
    zone_id                = aws_cloudfront_distribution.staff.hosted_zone_id
    evaluate_target_health = false
  }
}

# Customer sign frontend
resource "aws_route53_record" "sign" {
  zone_id = aws_route53_zone.main.zone_id
  name    = "sign.${var.domain_name}"
  type    = "A"
  alias {
    name                   = aws_cloudfront_distribution.customer.domain_name
    zone_id                = aws_cloudfront_distribution.customer.hosted_zone_id
    evaluate_target_health = false
  }
}

# Admin dashboard frontend
resource "aws_route53_record" "admin" {
  zone_id = aws_route53_zone.main.zone_id
  name    = "admin.${var.domain_name}"
  type    = "A"
  alias {
    name                   = aws_cloudfront_distribution.admin.domain_name
    zone_id                = aws_cloudfront_distribution.admin.hosted_zone_id
    evaluate_target_health = false
  }
}

# ACM certificate covers all subdomains
resource "aws_acm_certificate" "main" {
  domain_name               = var.domain_name
  subject_alternative_names = [
    "*.${var.domain_name}"
  ]
  validation_method = "DNS"

  lifecycle {
    create_before_destroy = true
  }
}

resource "aws_route53_record" "acm_validation" {
  for_each = {
    for dvo in aws_acm_certificate.main.domain_validation_options : dvo.domain_name => {
      name   = dvo.resource_record_name
      record = dvo.resource_record_value
      type   = dvo.resource_record_type
    }
  }
  zone_id = aws_route53_zone.main.zone_id
  name    = each.value.name
  type    = each.value.type
  ttl     = 60
  records = [each.value.record]
}

resource "aws_acm_certificate_validation" "main" {
  certificate_arn         = aws_acm_certificate.main.arn
  validation_record_fqdns = [for record in aws_route53_record.acm_validation : record.fqdn]
}
