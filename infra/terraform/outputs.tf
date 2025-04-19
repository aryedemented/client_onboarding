output "bucket_name" {
  value = aws_s3_bucket.recipe_bucket.id
}

# Output subnet for ECS task
output "private_subnet_id" {
  value = aws_subnet.private.id
}

output "vpc_id" {
  value = aws_vpc.main.id
}
