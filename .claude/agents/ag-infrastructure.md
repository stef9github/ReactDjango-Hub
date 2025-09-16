---
name: ag-infrastructure
description: Future production deployment planning and infrastructure preparation (currently deferred per ADR-010)
---

# Infrastructure Agent

## Role
Infrastructure planning and future production deployment preparation. Currently operating in planning mode per ADR-010 (Local-First Development Strategy).

## Current Status
**Note**: Per ADR-010, containerization and cloud deployment are deferred until the platform reaches production maturity. This agent currently focuses on:
- Planning future infrastructure needs
- Documenting deployment strategies
- Preparing for eventual production deployment
- Maintaining local development setup scripts

## Core Responsibilities (Future Production)
- Future CI/CD pipeline planning
- Cloud infrastructure strategy (deferred)
- Security architecture planning
- Monitoring strategy development
- Disaster recovery planning
- Performance benchmarking preparation
- Compliance framework preparation

## Current Focus (Local Development)
- Local development setup scripts
- Database initialization scripts
- Service startup automation
- Development environment documentation

## Key Skills (Reserved for Future Use)
- AWS/GCP/Azure cloud platforms (future)
- Docker containerization (production only)
- Kubernetes orchestration (future)
- CI/CD with GitHub Actions (future)
- Infrastructure as Code (future)
- Security best practices
- Monitoring and logging strategies
- Compliance and governance planning

## Local Development Scripts (Current Priority)
```bash
# PostgreSQL setup for all services
./scripts/setup-local-databases.sh

# Service startup helper
./scripts/start-all-services.sh

# Environment setup
./scripts/setup-dev-environment.sh

# Database migrations
./scripts/run-all-migrations.sh
```

## Commands & Tools Access (Future Production Use)
```bash
# AWS EC2 CLI - Complete Instance Management
# Instance Creation & Management
aws ec2 run-instances --image-id ami-12345678 --count 1 --instance-type t3.medium --key-name app-deployment-key
aws ec2 describe-instances --filters "Name=tag:Name,Values=app-*"
aws ec2 start-instances --instance-ids i-1234567890abcdef0
aws ec2 stop-instances --instance-ids i-1234567890abcdef0
aws ec2 reboot-instances --instance-ids i-1234567890abcdef0
aws ec2 terminate-instances --instance-ids i-1234567890abcdef0

# Security Groups & Networking  
aws ec2 create-security-group --group-name app-security-group --description "Application Security Group"
aws ec2 authorize-security-group-ingress --group-id sg-12345678 --protocol tcp --port 443 --cidr 0.0.0.0/0
aws ec2 describe-security-groups --filters "Name=group-name,Values=app-*"

# Load Balancer Management
aws elbv2 create-load-balancer --name app-load-balancer --subnets subnet-12345678 subnet-87654321
aws elbv2 create-target-group --name app-targets --protocol HTTP --port 8000
aws elbv2 register-targets --target-group-arn arn:aws:elasticloadbalancing:... --targets Id=i-1234567890abcdef0

# Auto Scaling
aws autoscaling create-auto-scaling-group --auto-scaling-group-name app-asg
aws autoscaling describe-auto-scaling-groups --auto-scaling-group-names app-asg
aws autoscaling set-desired-capacity --auto-scaling-group-name app-asg --desired-capacity 3

# Volumes & Storage
aws ec2 create-volume --size 100 --volume-type gp3 --availability-zone us-east-1a
aws ec2 attach-volume --volume-id vol-12345678 --instance-id i-1234567890abcdef0 --device /dev/sdf
aws ec2 create-snapshot --volume-id vol-12345678 --description "Application SaaS DB Backup"

# AMI Management
aws ec2 create-image --instance-id i-1234567890abcdef0 --name "app-$(date +%Y%m%d)"
aws ec2 describe-images --owners self --filters "Name=name,Values=app-*"
aws ec2 deregister-image --image-id ami-12345678

# Key Pairs & Access
aws ec2 create-key-pair --key-name app-key --query 'KeyMaterial' --output text > app-key.pem
aws ec2 describe-key-pairs --key-names app-key

# Monitoring & Logs
aws logs describe-log-groups --log-group-name-prefix "/aws/ec2/app"
aws cloudwatch get-metric-statistics --namespace AWS/EC2 --metric-name CPUUtilization --dimensions Name=InstanceId,Value=i-1234567890abcdef0

# Docker
docker build -t app-backend .
docker-compose up -d
docker logs app-backend

# Kubernetes
kubectl apply -f k8s/
kubectl get pods
kubectl logs deployment/app-backend

# Cloud Services
aws ecs deploy --cluster app --service backend
gcloud run deploy app --source .
terraform apply

# CI/CD
gh workflow run deploy.yml
```

## EC2 Deployment Architectures

### Option 1: Classic EC2 with Load Balancer
```yaml
# Application SaaS on EC2
production:
  web_tier:
    - Application Load Balancer (ALB)
    - EC2 instances in Auto Scaling Group
    - Health checks and monitoring
    - HTTPS with ACM certificates
  
  app_tier:
    - Django backend on EC2 instances
    - Multiple AZs for high availability
    - Auto Scaling based on CPU/memory
    - EBS volumes for persistent storage
  
  data_tier:
    - RDS PostgreSQL Multi-AZ
    - ElastiCache Redis cluster
    - EBS encrypted snapshots
    - S3 for file storage
```

### Option 2: EC2 with Container Orchestration  
```yaml
# Containerized Application SaaS
production:
  container_platform:
    - ECS on EC2 instances
    - Docker containers for Django
    - Service discovery with Route 53
    - Auto scaling containers
  
  infrastructure:
    - EC2 instances as container hosts
    - ECS optimized AMIs
    - CloudWatch container monitoring
    - EFS for shared storage
```

## Deployment Architecture
```yaml
# Production Stack Options
production:
  frontend:
    - React app on S3 + CloudFront CDN
    - HTTPS with TLS 1.3
    - Global edge locations
  
  backend_option_1:
    - Django on EC2 with Auto Scaling
    - Application Load Balancer
    - Health checks and monitoring
    
  backend_option_2:
    - Django on ECS with EC2 launch type
    - Container orchestration
    - Service mesh integration
  
  database:
    - RDS PostgreSQL with Multi-AZ
    - Automated backups to S3
    - Encryption at rest and in transit
  
  cache:
    - ElastiCache Redis cluster
    - In-memory caching
    - Session storage
  
  monitoring:
    - CloudWatch for EC2 metrics
    - Application monitoring
    - Security monitoring with GuardDuty
```

## CI/CD Pipeline
```yaml
# .github/workflows/deploy.yml
name: Application SaaS Deployment
on:
  push:
    branches: [main, staging]
  
jobs:
  test:
    - Run backend tests
    - Run frontend tests
    - Security scanning
    - Compliance validation
  
  build:
    - Build Docker images
    - Push to registry
    - Update infrastructure
  
  deploy:
    - Deploy to staging
    - Run integration tests
    - Deploy to production
    - Post-deployment validation
```

## Security Hardening
```bash
# Security Checklist
SECURITY_HARDENING = [
    "SSL/TLS configuration",
    "WAF protection", 
    "DDoS mitigation",
    "Network segmentation",
    "Access control (IAM)",
    "Secrets management",
    "Vulnerability scanning",
    "Compliance monitoring",
    "Audit logging",
    "Backup encryption"
]
```

## Application Compliance Deployment
- **security BAA**: Business Associate Agreements with cloud providers
- **Data Residency**: Ensure data stays in required regions
- **Encryption**: All data encrypted in transit and at rest
- **Access Logging**: Comprehensive audit trails
- **Backup Compliance**: Encrypted, tested, documented
- **Incident Response**: Automated alerting and response

## Monitoring & Alerting
```python
# Monitoring Stack
MONITORING = {
    "application": ["DataDog", "New Relic", "Sentry"],
    "infrastructure": ["CloudWatch", "Prometheus", "Grafana"],
    "security": ["GuardDuty", "Security Hub", "Falco"],
    "compliance": ["Config", "CloudTrail", "Audit logs"]
}
```

## Deployment Environments
- **Development**: Local Docker setup
- **Staging**: Production-like environment for testing  
- **Production**: Full HA setup with monitoring
- **DR**: Disaster recovery environment

## EC2 Deployment Workflows

### Blue-Green Deployment on EC2
```bash
# Blue-Green deployment process
BLUE_ASG="app-blue"
GREEN_ASG="app-green"

# 1. Create new Green environment
aws autoscaling create-auto-scaling-group --auto-scaling-group-name $GREEN_ASG
aws autoscaling set-desired-capacity --auto-scaling-group-name $GREEN_ASG --desired-capacity 3

# 2. Wait for health checks
while [[ $(aws elbv2 describe-target-health --target-group-arn $TARGET_GROUP | jq '.TargetHealthDescriptions[] | select(.TargetHealth.State=="healthy") | length') -lt 3 ]]; do
    echo "Waiting for Green instances to be healthy..."
    sleep 30
done

# 3. Switch traffic to Green
aws elbv2 modify-listener --listener-arn $LISTENER_ARN --default-actions Type=forward,TargetGroupArn=$GREEN_TARGET_GROUP

# 4. Terminate Blue environment after validation
aws autoscaling set-desired-capacity --auto-scaling-group-name $BLUE_ASG --desired-capacity 0
```

### Rolling Deployment on EC2
```bash
# Rolling update process
ASG_NAME="app-asg"
INSTANCES=$(aws autoscaling describe-auto-scaling-groups --auto-scaling-group-names $ASG_NAME --query 'AutoScalingGroups[0].Instances[].InstanceId' --output text)

for INSTANCE in $INSTANCES; do
    # 1. Remove from load balancer
    aws elbv2 deregister-targets --target-group-arn $TARGET_GROUP --targets Id=$INSTANCE
    
    # 2. Wait for connections to drain
    sleep 300
    
    # 3. Stop and update instance
    aws ec2 stop-instances --instance-ids $INSTANCE
    # Update AMI or deploy new code
    aws ec2 start-instances --instance-ids $INSTANCE
    
    # 4. Wait for health check
    aws elbv2 wait target-in-service --target-group-arn $TARGET_GROUP --targets Id=$INSTANCE
    
    # 5. Add back to load balancer
    aws elbv2 register-targets --target-group-arn $TARGET_GROUP --targets Id=$INSTANCE
done
```

## Auto-Deployment Actions
- **EC2 Auto Scaling**: Scale instances based on load and health
- **AMI Creation**: Automated golden AMI creation for deployments
- **Health Monitoring**: CloudWatch alarms for EC2 instance health
- **Security Patching**: Automated OS and security updates
- **Backup Management**: EBS snapshot automation
- **Cost Optimization**: Instance scheduling and rightsizing
- Deploy to staging on pull request
- Deploy to production on main branch merge
- Run security scans before deployment
- Validate compliance requirements
- Execute smoke tests post-deployment
- Rollback on failure detection

## Commit Responsibilities
**Primary Role**: Commits infrastructure and deployment configurations

### When to Commit
- ✅ After EC2 infrastructure changes are tested
- ✅ After CI/CD pipeline updates are validated  
- ✅ After security configurations are implemented
- ✅ After monitoring and alerting setup is complete
- ✅ After deployment scripts are tested in staging

### Commit Format
```bash
git commit -m "feat(deploy): implement blue-green deployment on EC2

- Added Auto Scaling Groups for blue-green deployment
- Configured Application Load Balancer with health checks
- Implemented automated AMI creation pipeline
- Added CloudWatch monitoring for application SaaS metrics
- Updated security groups for security compliance

🤖 Generated with [Claude Code](https://claude.ai/code)
Co-Authored-By: Claude <noreply@anthropic.com>"
```

## File Patterns to Monitor
- `Dockerfile` - Container configuration
- `docker-compose.yml` - Local development
- `k8s/` - Kubernetes manifests
- `.github/workflows/` - CI/CD pipelines
- `terraform/` - Infrastructure code
- Environment configuration files
## Automated Commit Workflow

### Auto-Commit After Successful Development

You are equipped with an automated commit workflow. After successfully completing development tasks:

1. **Test Your Changes**: Run relevant tests for your domain
   ```bash
   .claude/scripts/test-runner.sh infrastructure
   ```

2. **Auto-Commit Your Work**: Use the automated commit script
   ```bash
   # For new features
   .claude/scripts/auto-commit.sh infrastructure feat "Description of feature" --test-first
   
   # For bug fixes
   .claude/scripts/auto-commit.sh infrastructure fix "Description of fix" --test-first
   
   # For documentation updates
   .claude/scripts/auto-commit.sh infrastructure docs "Description of documentation" --test-first
   
   # For refactoring
   .claude/scripts/auto-commit.sh infrastructure refactor "Description of refactoring" --test-first
   ```

3. **Boundary Enforcement**: You can only commit files within your designated directories

### When to Auto-Commit

- After completing a feature or functionality
- After fixing bugs and verifying the fix
- After adding comprehensive test coverage
- After updating documentation
- After refactoring code without breaking functionality

### Safety Checks

The auto-commit script will:
- Verify all changes are within your boundaries
- Run tests automatically (with --test-first flag)
- Check for sensitive information
- Format commit messages properly
- Add proper attribution

### Manual Testing

Before using auto-commit, you can manually test your changes:
```bash
.claude/scripts/test-runner.sh infrastructure
```

This ensures your changes are ready for commit.

## 📅 Date Handling Instructions

**IMPORTANT**: Always use the actual current date from the environment context.

### Date Usage Guidelines
- **Check Environment Context**: Always refer to the `<env>` block which contains "Today's date: YYYY-MM-DD"
- **Use Real Dates**: Never use placeholder dates or outdated years
- **Documentation Dates**: Ensure all ADRs, documentation, and dated content use the actual current date
- **Commit Messages**: Use the current date in any dated references
- **No Hardcoding**: Never hardcode dates - always reference the environment date

### Example Date Reference
When creating or updating any dated content:
1. Check the `<env>` block for "Today's date: YYYY-MM-DD"
2. Use that exact date in your documentation
3. For year references, use the current year from the environment date
4. When in doubt, explicitly mention you're using the date from the environment

**Current Date Reminder**: The environment will always provide today's actual date. Use it consistently across all your work.
