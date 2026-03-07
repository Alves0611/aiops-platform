output "eks_cluster_arn" {
  value = aws_eks_cluster.this.arn
}

output "nginx_ingress_hostname" {
  value = data.kubernetes_service.nginx_ingress.status[0].load_balancer[0].ingress[0].hostname
}

output "app_url" {
  value = "http://app.${var.domain_name}"
}

output "grafana_url" {
  value = "http://grafana.${var.domain_name}"
}

output "loki_s3_bucket" {
  value = aws_s3_bucket.loki.id
}