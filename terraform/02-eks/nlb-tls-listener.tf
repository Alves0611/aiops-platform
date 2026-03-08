data "aws_lb" "nginx_ingress" {
  name = regex("^(?P<name>.+)-[^-]+$", split(".", data.kubernetes_service.nginx_ingress.status[0].load_balancer[0].ingress[0].hostname)[0]).name

  depends_on = [helm_release.nginx_ingress]
}

data "aws_lb_listener" "https" {
  load_balancer_arn = data.aws_lb.nginx_ingress.arn
  port              = 443
}

resource "null_resource" "nlb_tls_listener" {
  triggers = {
    listener_arn    = data.aws_lb_listener.https.arn
    certificate_arn = aws_acm_certificate.this.arn
  }

  provisioner "local-exec" {
    command = <<-EOT
      aws elbv2 modify-listener \
        --listener-arn "${data.aws_lb_listener.https.arn}" \
        --protocol TLS \
        --certificates CertificateArn="${aws_acm_certificate.this.arn}" \
        --region ${var.region}
    EOT
  }

  depends_on = [
    helm_release.nginx_ingress,
    aws_acm_certificate_validation.this,
  ]
}
