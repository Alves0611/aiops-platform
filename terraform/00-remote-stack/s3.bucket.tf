resource "aws_s3_bucket" "this" {
  bucket        = var.remote_backend.bucket_name

  tags          = { Name = var.remote_backend.bucket_name }
}
