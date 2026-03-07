data "aws_subnets" "private" {
  filter {
    name   = "tag:Name"
    values = ["studying-private-sub-1a", "studying-private-sub-1b"]
  }

  filter {
    name   = "map-public-ip-on-launch"
    values = [false]
  }
}
