# Fargate ECS Cluster and Task Definition for recipe pipeline

# ECS Cluster
resource "aws_ecs_cluster" "recipe_cluster" {
  name = "recipe-processing-cluster"
}

# IAM Role for Task Execution (allows ECS to pull from ECR, etc.)
resource "aws_iam_role" "ecs_task_execution_role" {
  name = "ecsTaskExecutionRole"

  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Action = "sts:AssumeRole",
        Effect = "Allow",
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
      }
    ]
  })
}

# Attach policies needed for ECS tasks
resource "aws_iam_role_policy_attachment" "ecs_execution_role_policy" {
  role       = aws_iam_role.ecs_task_execution_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

# ECS Task Definition
resource "aws_ecs_task_definition" "recipe_task" {
  family                   = "recipe-pipeline-task"
  requires_compatibilities = ["FARGATE"]
  network_mode            = "awsvpc"
  cpu                     = "512"
  memory                  = "1024"
  execution_role_arn      = aws_iam_role.ecs_task_execution_role.arn

  container_definitions = jsonencode([
    {
      name      = "recipe-pipeline"
      image     = "529088293486.dkr.ecr.eu-central-1.amazonaws.com/recipe-pipeline:latest"
      essential = true
      environment = [
        { name = "CLIENT_NAME", value = "italiano" },
        { name = "DISH_NAME", value = "bruschetta" },
        { name = "S3_BUCKET", value = "recipes-bucket-unique-123" },
#         { name = "OPENAI_API_KEY", value = "your-api-key" }
        { name = "DEEP_SEEK_API_KEY", value = "sk-115d62f80ee24840acce9f924431d47a"" }

      ]
      logConfiguration = {
        logDriver = "awslogs",
        options = {
          awslogs-group         = "/ecs/recipe-pipeline"
          awslogs-region        = var.region
          awslogs-stream-prefix = "ecs"
        }
      }
    }
  ])
}

# CloudWatch log group for ECS logging
resource "aws_cloudwatch_log_group" "recipe_pipeline_logs" {
  name              = "/ecs/recipe-pipeline"
  retention_in_days = 7
}

# ECS Service & VPC networking would be defined separately (optional for now)
# For one-off job execution, you'll likely trigger with `aws ecs run-task`
