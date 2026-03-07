variable "region" {
  type = string
  default = "us-east-1"
}

variable "default_tags" {
  type = object({
    ManagedBy = string
  })

  default = {
    ManagedBy = "Terraform"
  }
}

variable "remote_backend" {
  type = object({
    dynamo_table_name          = string
    dynamo_table_billing_mode  = string
    dynamo_table_hash_key      = string
    dynamo_table_hash_key_type = string
    bucket_name                = string
  })

  default = {
    dynamo_table_name          = "state-locking-444065722670"
    dynamo_table_billing_mode  = "PAY_PER_REQUEST"
    dynamo_table_hash_key      = "LockID"
    dynamo_table_hash_key_type = "S"
    bucket_name                = "tfstate-444065722670"
  }
}
