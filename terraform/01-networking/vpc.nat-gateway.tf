resource "aws_nat_gateway" "this" {
  count = var.enable_nat_gateway ? 1 : 0

  allocation_id = aws_eip.this[0].id
  subnet_id     = aws_subnet.public[0].id

  tags = { Name = var.vpc.nat_gateway_name }

  depends_on = [aws_internet_gateway.this]
}
