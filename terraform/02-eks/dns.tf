data "aws_route53_zone" "this" {
  name         = var.domain_name
  private_zone = false
}

data "kubernetes_service" "nginx_ingress" {
  metadata {
    name      = "ingress-nginx-controller"
    namespace = helm_release.nginx_ingress.namespace
  }

  depends_on = [helm_release.nginx_ingress]
}

resource "aws_route53_record" "app" {
  zone_id = data.aws_route53_zone.this.zone_id
  name    = "app.${var.domain_name}"
  type    = "CNAME"
  ttl     = 300
  records = [data.kubernetes_service.nginx_ingress.status[0].load_balancer[0].ingress[0].hostname]
}

resource "aws_route53_record" "grafana" {
  zone_id = data.aws_route53_zone.this.zone_id
  name    = "grafana.${var.domain_name}"
  type    = "CNAME"
  ttl     = 300
  records = [data.kubernetes_service.nginx_ingress.status[0].load_balancer[0].ingress[0].hostname]
}
