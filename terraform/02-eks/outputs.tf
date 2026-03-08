output "eks_cluster_arn" {
  value = aws_eks_cluster.this.arn
}

output "nginx_ingress_hostname" {
  value = data.kubernetes_service.nginx_ingress.status[0].load_balancer[0].ingress[0].hostname
}

output "app_url" {
  value = "https://app.${var.domain_name}"
}

output "grafana_url" {
  value = "https://grafana.${var.domain_name}"
}

output "acm_certificate_arn" {
  value = aws_acm_certificate.this.arn
}

output "loki_s3_bucket" {
  value = aws_s3_bucket.loki.id
}

output "loki_role_arn" {
  value = aws_iam_role.loki.arn
}