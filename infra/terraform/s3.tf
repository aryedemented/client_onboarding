resource "aws_s3_bucket" "recipe_bucket" {
  bucket = var.bucket_name

  tags = {
    Name        = "Recipe Storage Bucket"
    Environment = "dev"
  }
}

resource "aws_s3_bucket_public_access_block" "recipe_block" {
  bucket = aws_s3_bucket.recipe_bucket.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}
