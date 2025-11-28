# EC2 Module Outputs

output "instance_id" {
  description = "ID of the EC2 instance"
  value       = aws_instance.app.id
}

output "private_ip" {
  description = "Private IP of the EC2 instance"
  value       = aws_instance.app.private_ip
}

# ALB outputs - commented out until AWS enables ELB service
# output "alb_dns_name" {
#   description = "DNS name of the Application Load Balancer"
#   value       = aws_lb.main.dns_name
# }
#
# output "alb_arn" {
#   description = "ARN of the Application Load Balancer"
#   value       = aws_lb.main.arn
# }
#
# output "target_group_arn" {
#   description = "ARN of the target group"
#   value       = aws_lb_target_group.app.arn
# }
