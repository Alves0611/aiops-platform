resource "aws_iam_role" "loki" {
  name = "EKS_Loki_Role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = "sts:AssumeRoleWithWebIdentity"
      Principal = {
        Federated = aws_iam_openid_connect_provider.kubernetes.arn
      }
      Condition = {
        StringEquals = {
          "${replace(aws_eks_cluster.this.identity[0].oidc[0].issuer, "https://", "")}:aud" = "sts.amazonaws.com"
          "${replace(aws_eks_cluster.this.identity[0].oidc[0].issuer, "https://", "")}:sub" = "system:serviceaccount:logging:loki"
        }
      }
    }]
  })
}

resource "aws_iam_role_policy_attachment" "loki_s3" {
  policy_arn = aws_iam_policy.loki_s3.arn
  role       = aws_iam_role.loki.name
}
