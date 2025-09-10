# Medical SaaS Infrastructure Outputs

# Network Outputs
output "vpc_id" {
  description = "ID of the VPC"
  value       = aws_vpc.medical_vpc.id
}

output "vpc_cidr_block" {
  description = "CIDR block of the VPC"
  value       = aws_vpc.medical_vpc.cidr_block
}

output "public_subnet_ids" {
  description = "IDs of the public subnets"
  value       = aws_subnet.public_subnets[*].id
}

output "private_subnet_ids" {
  description = "IDs of the private subnets"
  value       = aws_subnet.private_subnets[*].id
}

output "database_subnet_ids" {
  description = "IDs of the database subnets"
  value       = aws_subnet.database_subnets[*].id
}

output "internet_gateway_id" {
  description = "ID of the Internet Gateway"
  value       = aws_internet_gateway.medical_igw.id
}

output "nat_gateway_ids" {
  description = "IDs of the NAT Gateways"
  value       = aws_nat_gateway.medical_nat_gws[*].id
}

# Security Group Outputs
output "alb_security_group_id" {
  description = "ID of the Application Load Balancer security group"
  value       = aws_security_group.alb_security_group.id
}

output "ecs_security_group_id" {
  description = "ID of the ECS security group"
  value       = aws_security_group.ecs_security_group.id
}

output "rds_security_group_id" {
  description = "ID of the RDS security group"
  value       = aws_security_group.rds_security_group.id
}

# Load Balancer Outputs
output "alb_id" {
  description = "ID of the Application Load Balancer"
  value       = aws_lb.medical_alb.id
}

output "alb_arn" {
  description = "ARN of the Application Load Balancer"
  value       = aws_lb.medical_alb.arn
}

output "alb_dns_name" {
  description = "DNS name of the Application Load Balancer"
  value       = aws_lb.medical_alb.dns_name
}

output "alb_zone_id" {
  description = "Zone ID of the Application Load Balancer"
  value       = aws_lb.medical_alb.zone_id
}

# ECS Cluster Outputs
output "ecs_cluster_id" {
  description = "ID of the ECS cluster"
  value       = aws_ecs_cluster.medical_cluster.id
}

output "ecs_cluster_arn" {
  description = "ARN of the ECS cluster"
  value       = aws_ecs_cluster.medical_cluster.arn
}

output "ecs_cluster_name" {
  description = "Name of the ECS cluster"
  value       = aws_ecs_cluster.medical_cluster.name
}

# Database Outputs
output "rds_endpoint" {
  description = "RDS instance endpoint"
  value       = aws_db_instance.medical_postgres.endpoint
  sensitive   = false
}

output "rds_port" {
  description = "RDS instance port"
  value       = aws_db_instance.medical_postgres.port
}

output "database_name" {
  description = "Name of the database"
  value       = aws_db_instance.medical_postgres.db_name
}

output "database_username" {
  description = "Database master username"
  value       = aws_db_instance.medical_postgres.username
  sensitive   = false
}

output "rds_instance_id" {
  description = "ID of the RDS instance"
  value       = aws_db_instance.medical_postgres.id
}

output "rds_resource_id" {
  description = "Resource ID of the RDS instance"
  value       = aws_db_instance.medical_postgres.resource_id
}

# Redis Outputs
output "redis_endpoint" {
  description = "Redis cluster endpoint"
  value       = aws_elasticache_replication_group.medical_redis.configuration_endpoint_address
}

output "redis_port" {
  description = "Redis cluster port"
  value       = aws_elasticache_replication_group.medical_redis.port
}

output "redis_cluster_id" {
  description = "ID of the Redis cluster"
  value       = aws_elasticache_replication_group.medical_redis.replication_group_id
}

# S3 Outputs
output "s3_bucket_name" {
  description = "Name of the S3 bucket for frontend assets"
  value       = aws_s3_bucket.medical_frontend_bucket.bucket
}

output "s3_bucket_arn" {
  description = "ARN of the S3 bucket for frontend assets"
  value       = aws_s3_bucket.medical_frontend_bucket.arn
}

output "s3_bucket_domain_name" {
  description = "Domain name of the S3 bucket"
  value       = aws_s3_bucket.medical_frontend_bucket.bucket_domain_name
}

# KMS Outputs
output "kms_key_id" {
  description = "ID of the KMS key"
  value       = aws_kms_key.medical_kms_key.key_id
}

output "kms_key_arn" {
  description = "ARN of the KMS key"
  value       = aws_kms_key.medical_kms_key.arn
}

output "kms_alias_name" {
  description = "Name of the KMS key alias"
  value       = aws_kms_alias.medical_kms_alias.name
}

# CloudWatch Outputs
output "cloudwatch_log_group_name" {
  description = "Name of the CloudWatch log group"
  value       = aws_cloudwatch_log_group.ecs_log_group.name
}

output "cloudwatch_log_group_arn" {
  description = "ARN of the CloudWatch log group"
  value       = aws_cloudwatch_log_group.ecs_log_group.arn
}

# Application URLs and Connection Information
output "application_url" {
  description = "Application URL (Load Balancer DNS name)"
  value       = "https://${aws_lb.medical_alb.dns_name}"
}

output "database_url" {
  description = "Database connection URL (without password)"
  value       = "postgresql://${aws_db_instance.medical_postgres.username}@${aws_db_instance.medical_postgres.endpoint}:${aws_db_instance.medical_postgres.port}/${aws_db_instance.medical_postgres.db_name}"
  sensitive   = false
}

output "redis_url" {
  description = "Redis connection URL"
  value       = "redis://${aws_elasticache_replication_group.medical_redis.configuration_endpoint_address}:${aws_elasticache_replication_group.medical_redis.port}"
  sensitive   = false
}

# Environment Information
output "environment" {
  description = "Environment name"
  value       = var.environment
}

output "project_name" {
  description = "Project name"
  value       = var.project_name
}

output "aws_region" {
  description = "AWS region"
  value       = var.aws_region
}

# Security and Compliance Information
output "encryption_enabled" {
  description = "Whether encryption is enabled for all resources"
  value       = var.enable_encryption
}

output "backup_retention_days" {
  description = "Number of days backups are retained"
  value       = local.merged_config.backup_retention_days
}

output "deletion_protection_enabled" {
  description = "Whether deletion protection is enabled"
  value       = local.merged_config.enable_deletion_protection
}

# Resource Tags
output "common_tags" {
  description = "Common tags applied to all resources"
  value       = local.common_tags
}

# Deployment Information for CI/CD
output "deployment_info" {
  description = "Deployment information for CI/CD pipelines"
  value = {
    cluster_name    = aws_ecs_cluster.medical_cluster.name
    alb_dns_name    = aws_lb.medical_alb.dns_name
    s3_bucket_name  = aws_s3_bucket.medical_frontend_bucket.bucket
    vpc_id          = aws_vpc.medical_vpc.id
    private_subnets = aws_subnet.private_subnets[*].id
    security_groups = {
      alb = aws_security_group.alb_security_group.id
      ecs = aws_security_group.ecs_security_group.id
      rds = aws_security_group.rds_security_group.id
    }
    log_group_name = aws_cloudwatch_log_group.ecs_log_group.name
  }
  sensitive = false
}

# Monitoring and Alerting Information
output "monitoring_info" {
  description = "Monitoring and alerting configuration"
  value = {
    cloudwatch_log_group    = aws_cloudwatch_log_group.ecs_log_group.name
    cloudwatch_retention    = local.merged_config.cloudwatch_retention_days
    high_cpu_alarm         = aws_cloudwatch_metric_alarm.high_cpu.alarm_name
    kms_encryption_key     = aws_kms_key.medical_kms_key.arn
  }
  sensitive = false
}