variable "region" {
  type    = string
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

variable "enable_nat_gateway" {
  type    = bool
  default = true
}

variable "vpc" {
  type = object({
    name                     = string
    cidr_block               = string
    internet_gateway_name    = string
    nat_gateway_name         = string
    public_route_table_name  = string
    private_route_table_name = string
    public_subnets = list(object({
      name              = string
      cidr_block        = string
      availability_zone = string
    }))
    private_subnets = list(object({
      name              = string
      cidr_block        = string
      availability_zone = string
    }))
  })

  default = {
    name                     = "studying-vpc"
    cidr_block               = "10.0.0.0/16"
    internet_gateway_name    = "studying-igw"
    nat_gateway_name         = "studying-ngw"
    public_route_table_name  = "studying-public-rt"
    private_route_table_name = "studying-private-rt"
    public_subnets = [
      {
        name              = "studying-public-sub-1a"
        cidr_block        = "10.0.1.0/24"
        availability_zone = "us-east-1a"
      },
      {
        name              = "studying-public-sub-1b"
        cidr_block        = "10.0.2.0/24"
        availability_zone = "us-east-1b"
      },
      {
        name              = "studying-public-sub-1c"
        cidr_block        = "10.0.3.0/24"
        availability_zone = "us-east-1c"
      },
    ]
    private_subnets = [
      {
        name              = "studying-private-sub-1a"
        cidr_block        = "10.0.10.0/24"
        availability_zone = "us-east-1a"
      },
      {
        name              = "studying-private-sub-1b"
        cidr_block        = "10.0.11.0/24"
        availability_zone = "us-east-1b"
      },
      {
        name              = "studying-private-sub-1c"
        cidr_block        = "10.0.12.0/24"
        availability_zone = "us-east-1c"
      },
    ]
  }
}
