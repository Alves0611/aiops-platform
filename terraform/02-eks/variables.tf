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

variable "domain_name" {
  type    = string
  default = "gabrielstudying.click"
}

variable "eks_cluster" {
  type = object({
    name                                   = string
    version                                = string
    access_config_authentication_mode      = string
    node_group_name                        = string
    node_group_capacity_type               = string
    node_group_instance_types              = list(string)
    node_group_scaling_config_desired_size = number
    node_group_scaling_config_max_size     = number
    node_group_scaling_config_min_size     = number
  })

  default = {
    name                                   = "studying-cluster"
    version                                = "1.34"
    access_config_authentication_mode      = "API_AND_CONFIG_MAP"
    node_group_name                        = "studying-node-group"
    node_group_capacity_type               = "ON_DEMAND"
    node_group_instance_types              = ["t3.medium"]
    node_group_scaling_config_desired_size = 2
    node_group_scaling_config_max_size     = 2
    node_group_scaling_config_min_size     = 2
  }
}
