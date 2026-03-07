output "s3_bucket_name" {
  value = aws_s3_bucket.this.bucket_domain_name
}

output "dynamo_table_name" {
  value = aws_dynamodb_table.this.name
}