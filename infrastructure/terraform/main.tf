# Medical SaaS Infrastructure - Main Configuration
terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
  
  default_tags {
    tags = {
      Project     = "ReactDjango-Hub-Medical-SaaS"
      Environment = var.environment
      ManagedBy   = "Terraform"
      Compliance  = "HIPAA-Ready"
    }
  }
}

# VPC Configuration for Medical SaaS
resource "aws_vpc" "medical_vpc" {
  cidr_block           = var.vpc_cidr
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Name = "${var.project_name}-vpc-${var.environment}"
  }
}

# Public Subnets for Load Balancers
resource "aws_subnet" "public_subnets" {
  count             = length(var.availability_zones)
  vpc_id            = aws_vpc.medical_vpc.id
  cidr_block        = var.public_subnet_cidrs[count.index]
  availability_zone = var.availability_zones[count.index]
  
  map_public_ip_on_launch = true

  tags = {
    Name = "${var.project_name}-public-${var.availability_zones[count.index]}-${var.environment}"
    Type = "Public"
  }
}

# Private Subnets for Application Services
resource "aws_subnet" "private_subnets" {
  count             = length(var.availability_zones)
  vpc_id            = aws_vpc.medical_vpc.id
  cidr_block        = var.private_subnet_cidrs[count.index]
  availability_zone = var.availability_zones[count.index]

  tags = {
    Name = "${var.project_name}-private-${var.availability_zones[count.index]}-${var.environment}"
    Type = "Private"
  }
}

# Database Subnets for RDS
resource "aws_subnet" "database_subnets" {
  count             = length(var.availability_zones)
  vpc_id            = aws_vpc.medical_vpc.id
  cidr_block        = var.database_subnet_cidrs[count.index]
  availability_zone = var.availability_zones[count.index]

  tags = {
    Name = "${var.project_name}-database-${var.availability_zones[count.index]}-${var.environment}"
    Type = "Database"
  }
}

# Internet Gateway
resource "aws_internet_gateway" "medical_igw" {
  vpc_id = aws_vpc.medical_vpc.id

  tags = {
    Name = "${var.project_name}-igw-${var.environment}"
  }
}

# NAT Gateways for Private Subnets
resource "aws_eip" "nat_eips" {
  count  = length(var.availability_zones)
  domain = "vpc"

  tags = {
    Name = "${var.project_name}-nat-eip-${var.availability_zones[count.index]}-${var.environment}"
  }

  depends_on = [aws_internet_gateway.medical_igw]
}

resource "aws_nat_gateway" "medical_nat_gws" {
  count         = length(var.availability_zones)
  allocation_id = aws_eip.nat_eips[count.index].id
  subnet_id     = aws_subnet.public_subnets[count.index].id

  tags = {
    Name = "${var.project_name}-nat-gw-${var.availability_zones[count.index]}-${var.environment}"
  }

  depends_on = [aws_internet_gateway.medical_igw]
}

# Route Tables
resource "aws_route_table" "public_route_table" {
  vpc_id = aws_vpc.medical_vpc.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.medical_igw.id
  }

  tags = {
    Name = "${var.project_name}-public-rt-${var.environment}"
  }
}

resource "aws_route_table" "private_route_tables" {
  count  = length(var.availability_zones)
  vpc_id = aws_vpc.medical_vpc.id

  route {
    cidr_block     = "0.0.0.0/0"
    nat_gateway_id = aws_nat_gateway.medical_nat_gws[count.index].id
  }

  tags = {
    Name = "${var.project_name}-private-rt-${var.availability_zones[count.index]}-${var.environment}"
  }
}

# Route Table Associations
resource "aws_route_table_association" "public_associations" {
  count          = length(aws_subnet.public_subnets)
  subnet_id      = aws_subnet.public_subnets[count.index].id
  route_table_id = aws_route_table.public_route_table.id
}

resource "aws_route_table_association" "private_associations" {
  count          = length(aws_subnet.private_subnets)
  subnet_id      = aws_subnet.private_subnets[count.index].id
  route_table_id = aws_route_table.private_route_tables[count.index].id
}

# Security Groups
resource "aws_security_group" "alb_security_group" {
  name_prefix = "${var.project_name}-alb-"
  vpc_id      = aws_vpc.medical_vpc.id

  ingress {
    description = "HTTP"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "HTTPS"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.project_name}-alb-sg-${var.environment}"
  }

  lifecycle {
    create_before_destroy = true
  }
}

resource "aws_security_group" "ecs_security_group" {
  name_prefix = "${var.project_name}-ecs-"
  vpc_id      = aws_vpc.medical_vpc.id

  ingress {
    description     = "HTTP from ALB"
    from_port       = 8000
    to_port         = 8000
    protocol        = "tcp"
    security_groups = [aws_security_group.alb_security_group.id]
  }

  ingress {
    description     = "Identity Service from ALB"
    from_port       = 8001
    to_port         = 8001
    protocol        = "tcp"
    security_groups = [aws_security_group.alb_security_group.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.project_name}-ecs-sg-${var.environment}"
  }

  lifecycle {
    create_before_destroy = true
  }
}

resource "aws_security_group" "rds_security_group" {
  name_prefix = "${var.project_name}-rds-"
  vpc_id      = aws_vpc.medical_vpc.id

  ingress {
    description     = "PostgreSQL from ECS"
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.ecs_security_group.id]
  }

  tags = {
    Name = "${var.project_name}-rds-sg-${var.environment}"
  }

  lifecycle {
    create_before_destroy = true
  }
}

# ECS Cluster
resource "aws_ecs_cluster" "medical_cluster" {
  name = "${var.project_name}-cluster-${var.environment}"

  setting {
    name  = "containerInsights"
    value = "enabled"
  }

  tags = {
    Name = "${var.project_name}-cluster-${var.environment}"
  }
}

# Application Load Balancer
resource "aws_lb" "medical_alb" {
  name               = "${var.project_name}-alb-${var.environment}"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb_security_group.id]
  subnets            = aws_subnet.public_subnets[*].id

  enable_deletion_protection = var.environment == "production" ? true : false

  tags = {
    Name = "${var.project_name}-alb-${var.environment}"
  }
}

# Database Subnet Group
resource "aws_db_subnet_group" "medical_db_subnet_group" {
  name       = "${var.project_name}-db-subnet-group-${var.environment}"
  subnet_ids = aws_subnet.database_subnets[*].id

  tags = {
    Name = "${var.project_name}-db-subnet-group-${var.environment}"
  }
}

# RDS PostgreSQL Instance (HIPAA-Ready Configuration)
resource "aws_db_instance" "medical_postgres" {
  identifier     = "${var.project_name}-postgres-${var.environment}"
  engine         = "postgres"
  engine_version = var.postgres_version
  instance_class = var.db_instance_class
  
  allocated_storage     = var.db_allocated_storage
  max_allocated_storage = var.db_max_allocated_storage
  storage_type          = "gp3"
  storage_encrypted     = true
  kms_key_id           = aws_kms_key.medical_kms_key.arn

  db_name  = var.database_name
  username = var.database_username
  password = var.database_password

  vpc_security_group_ids = [aws_security_group.rds_security_group.id]
  db_subnet_group_name   = aws_db_subnet_group.medical_db_subnet_group.name

  backup_retention_period = var.environment == "production" ? 30 : 7
  backup_window          = "03:00-04:00"
  maintenance_window     = "sun:04:00-sun:05:00"

  multi_az               = var.environment == "production" ? true : false
  publicly_accessible    = false
  auto_minor_version_upgrade = true

  deletion_protection = var.environment == "production" ? true : false
  skip_final_snapshot = var.environment != "production"
  final_snapshot_identifier = var.environment == "production" ? "${var.project_name}-postgres-final-snapshot-${var.environment}" : null

  tags = {
    Name = "${var.project_name}-postgres-${var.environment}"
    Compliance = "HIPAA-Ready"
  }
}

# KMS Key for Encryption
resource "aws_kms_key" "medical_kms_key" {
  description             = "KMS key for ${var.project_name} ${var.environment} encryption"
  deletion_window_in_days = 7
  enable_key_rotation     = true

  tags = {
    Name = "${var.project_name}-kms-key-${var.environment}"
    Compliance = "HIPAA-Ready"
  }
}

resource "aws_kms_alias" "medical_kms_alias" {
  name          = "alias/${var.project_name}-${var.environment}"
  target_key_id = aws_kms_key.medical_kms_key.key_id
}

# ElastiCache Redis Subnet Group
resource "aws_elasticache_subnet_group" "medical_redis_subnet_group" {
  name       = "${var.project_name}-redis-subnet-group-${var.environment}"
  subnet_ids = aws_subnet.private_subnets[*].id

  tags = {
    Name = "${var.project_name}-redis-subnet-group-${var.environment}"
  }
}

# ElastiCache Redis Cluster
resource "aws_elasticache_replication_group" "medical_redis" {
  description          = "Redis cluster for ${var.project_name} ${var.environment}"
  replication_group_id = "${var.project_name}-redis-${var.environment}"
  
  port                   = 6379
  parameter_group_name   = "default.redis7"
  engine_version        = "7.0"
  node_type             = var.redis_node_type
  num_cache_clusters    = var.redis_num_cache_nodes
  
  subnet_group_name  = aws_elasticache_subnet_group.medical_redis_subnet_group.name
  security_group_ids = [aws_security_group.ecs_security_group.id]
  
  at_rest_encryption_enabled = true
  transit_encryption_enabled = true
  auth_token                 = var.redis_auth_token
  
  tags = {
    Name = "${var.project_name}-redis-${var.environment}"
    Compliance = "HIPAA-Ready"
  }
}

# S3 Bucket for Frontend Static Assets
resource "aws_s3_bucket" "medical_frontend_bucket" {
  bucket = "${var.project_name}-frontend-${var.environment}-${random_string.bucket_suffix.result}"

  tags = {
    Name = "${var.project_name}-frontend-${var.environment}"
  }
}

resource "random_string" "bucket_suffix" {
  length  = 8
  special = false
  upper   = false
}

resource "aws_s3_bucket_versioning" "medical_frontend_versioning" {
  bucket = aws_s3_bucket.medical_frontend_bucket.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "medical_frontend_encryption" {
  bucket = aws_s3_bucket.medical_frontend_bucket.id

  rule {
    apply_server_side_encryption_by_default {
      kms_master_key_id = aws_kms_key.medical_kms_key.arn
      sse_algorithm     = "aws:kms"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "medical_frontend_pab" {
  bucket = aws_s3_bucket.medical_frontend_bucket.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# CloudWatch Log Groups
resource "aws_cloudwatch_log_group" "ecs_log_group" {
  name              = "/ecs/${var.project_name}-${var.environment}"
  retention_in_days = var.environment == "production" ? 30 : 7
  kms_key_id        = aws_kms_key.medical_kms_key.arn

  tags = {
    Name = "${var.project_name}-ecs-logs-${var.environment}"
  }
}

# CloudWatch Alarms for Monitoring
resource "aws_cloudwatch_metric_alarm" "high_cpu" {
  alarm_name          = "${var.project_name}-high-cpu-${var.environment}"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "CPUUtilization"
  namespace           = "AWS/ECS"
  period              = "120"
  statistic           = "Average"
  threshold           = "80"
  alarm_description   = "This metric monitors ecs cpu utilization"
  alarm_actions       = [] # Add SNS topic ARN here

  dimensions = {
    ServiceName = "${var.project_name}-backend-service"
    ClusterName = aws_ecs_cluster.medical_cluster.name
  }

  tags = {
    Name = "${var.project_name}-high-cpu-alarm-${var.environment}"
  }
}