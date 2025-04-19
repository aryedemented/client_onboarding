# ECS Service using private subnet with NAT
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
