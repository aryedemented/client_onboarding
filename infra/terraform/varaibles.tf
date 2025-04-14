variable "region" {
  description = "AWS region"
  type        = string
  default     = "eu-central-1"
}

variable "bucket_name" {
  description = "Raw Recipes S3 bucket name"
  type        = string
}
