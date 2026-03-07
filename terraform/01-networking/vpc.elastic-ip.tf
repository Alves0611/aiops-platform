resource "aws_eip" "this" {
  count = var.enable_nat_gateway ? 1 : 0

  domain = "vpc"
  tags   = { Name = var.vpc.nat_gateway_name }
}
