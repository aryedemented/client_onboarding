# ECS Service using private subnet with NAT
resource "aws_ecs_task_definition" "recipe_task" {
  family                   = "recipe-pipeline-task"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = "512"
  memory                   = "1024"
  execution_role_arn       = aws_iam_role.ecs_task_execution_role.arn

  container_definitions = jsonencode([
    {
      name      = "recipe-pipeline"
      image     = "your-ecr-url/recipe-pipeline:latest"
      essential = true
      environment = [
        { name = "CLIENT_NAME", value = "italiano" },
        { name = "DISH_NAME", value = "bruschetta" },
        { name = "S3_BUCKET", value = "your-s3-bucket-name" }
      ]
    }
  ])
}


resource "aws_ecs_service" "recipe_service" {
  name            = "recipe-service"
  cluster         = aws_ecs_cluster.recipe_cluster.id
  task_definition = aws_ecs_task_definition.recipe_task.arn
  launch_type     = "FARGATE"
  desired_count   = 1

  network_configuration {
    subnets          = [aws_subnet.private.id]
    assign_public_ip = false
    security_groups  = [aws_security_group.recipe_sg.id] # define this in your security group file
  }

  depends_on = [
    aws_ecs_cluster.recipe_cluster,
    aws_ecs_task_definition.recipe_task
  ]
}

resource "aws_ecs_cluster" "recipe_cluster" {
  name = "recipe-processing-cluster"
}
