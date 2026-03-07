resource "aws_ecr_repository" "traffic_simulator" {
  name                 = "traffic-simulator"
  image_tag_mutability = "MUTABLE"
  force_delete         = true

  image_scanning_configuration {
    scan_on_push = false
  }
}
