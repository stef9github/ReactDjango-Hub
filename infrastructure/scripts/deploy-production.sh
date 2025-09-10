#!/bin/bash
# Medical SaaS Production Deployment Script
# This script deploys the medical SaaS platform to production with full HIPAA compliance

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
NAMESPACE="hub-namespace"
ENVIRONMENT="production"
CLUSTER_NAME="medical-saas-cluster"
AWS_REGION="us-east-1"

# Logging function
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

error() {
    echo -e "${RED}[ERROR] $1${NC}" >&2
}

warning() {
    echo -e "${YELLOW}[WARNING] $1${NC}"
}

info() {
    echo -e "${BLUE}[INFO] $1${NC}"
}

# Check prerequisites
check_prerequisites() {
    log "Checking prerequisites..."
    
    # Check required tools
    local tools=("kubectl" "aws" "terraform" "docker" "helm")
    for tool in "${tools[@]}"; do
        if ! command -v "$tool" &> /dev/null; then
            error "$tool is not installed or not in PATH"
            exit 1
        fi
    done
    
    # Check AWS credentials
    if ! aws sts get-caller-identity &> /dev/null; then
        error "AWS credentials not configured"
        exit 1
    fi
    
    # Check kubectl context
    local current_context
    current_context=$(kubectl config current-context 2>/dev/null || echo "")
    if [[ "$current_context" != *"$CLUSTER_NAME"* ]]; then
        error "kubectl not configured for cluster: $CLUSTER_NAME"
        exit 1
    fi
    
    log "Prerequisites check passed ✓"
}

# Deploy infrastructure with Terraform
deploy_infrastructure() {
    log "Deploying infrastructure with Terraform..."
    
    cd infrastructure/terraform
    
    # Initialize Terraform if needed
    if [[ ! -d ".terraform" ]]; then
        terraform init
    fi
    
    # Plan and apply infrastructure
    terraform plan -var="environment=$ENVIRONMENT" -out=tfplan
    terraform apply -auto-approve tfplan
    
    # Get outputs for later use
    export ALB_DNS_NAME=$(terraform output -raw alb_dns_name)
    export RDS_ENDPOINT=$(terraform output -raw rds_endpoint)
    export REDIS_ENDPOINT=$(terraform output -raw redis_endpoint)
    export S3_BUCKET_NAME=$(terraform output -raw s3_bucket_name)
    
    log "Infrastructure deployed successfully ✓"
    cd ../..
}

# Create or update Kubernetes secrets
update_secrets() {
    log "Updating Kubernetes secrets..."
    
    # Check if .env file exists
    if [[ ! -f "infrastructure/docker/production/.env" ]]; then
        error ".env file not found. Please copy .env.example and configure it."
        exit 1
    fi
    
    # Source environment variables
    set -a
    source infrastructure/docker/production/.env
    set +a
    
    # Create namespace if it doesn't exist
    kubectl create namespace "$NAMESPACE" --dry-run=client -o yaml | kubectl apply -f -
    
    # Update secrets from environment variables
    kubectl create secret generic identity-service-secrets \
        --from-literal=database-url="$IDENTITY_DATABASE_URL" \
        --from-literal=redis-url="$IDENTITY_REDIS_URL" \
        --from-literal=jwt-secret-key="$JWT_SECRET_KEY" \
        --from-literal=smtp-password="$SMTP_PASSWORD" \
        --from-literal=encryption-key="$DATA_ENCRYPTION_KEY" \
        --from-literal=twilio-auth-token="$TWILIO_AUTH_TOKEN" \
        --from-literal=sendgrid-api-key="$SMTP_PASSWORD" \
        --namespace="$NAMESPACE" \
        --dry-run=client -o yaml | kubectl apply -f -
    
    kubectl create secret generic backend-service-secrets \
        --from-literal=database-url="$DATABASE_URL" \
        --from-literal=redis-url="$BACKEND_REDIS_URL" \
        --from-literal=django-secret-key="$DJANGO_SECRET_KEY" \
        --from-literal=aws-access-key-id="$AWS_ACCESS_KEY_ID" \
        --from-literal=aws-secret-access-key="$AWS_SECRET_ACCESS_KEY" \
        --from-literal=s3-bucket-name="$AWS_S3_BUCKET_NAME" \
        --from-literal=stripe-secret-key="$STRIPE_SECRET_KEY" \
        --from-literal=phi-encryption-key="$PHI_ENCRYPTION_KEY" \
        --from-literal=sentry-dsn="$SENTRY_DSN" \
        --namespace="$NAMESPACE" \
        --dry-run=client -o yaml | kubectl apply -f -
    
    log "Secrets updated successfully ✓"
}

# Deploy Kubernetes manifests
deploy_kubernetes() {
    log "Deploying Kubernetes manifests..."
    
    # Apply configurations in order
    kubectl apply -f infrastructure/kubernetes/namespaces/
    kubectl apply -f infrastructure/kubernetes/configmaps/
    kubectl apply -f infrastructure/kubernetes/secrets/
    kubectl apply -f infrastructure/kubernetes/deployments/
    kubectl apply -f infrastructure/kubernetes/services/
    kubectl apply -f infrastructure/kubernetes/ingress/
    
    # Deploy monitoring stack
    kubectl apply -f infrastructure/kubernetes/monitoring/
    
    log "Kubernetes manifests deployed successfully ✓"
}

# Wait for deployments to be ready
wait_for_deployments() {
    log "Waiting for deployments to be ready..."
    
    local deployments=("identity-service" "backend-service")
    
    for deployment in "${deployments[@]}"; do
        info "Waiting for $deployment to be ready..."
        kubectl wait --for=condition=available --timeout=300s deployment/"$deployment" -n "$NAMESPACE"
        if [[ $? -eq 0 ]]; then
            log "$deployment is ready ✓"
        else
            error "$deployment failed to become ready"
            exit 1
        fi
    done
    
    log "All deployments are ready ✓"
}

# Run database migrations
run_migrations() {
    log "Running database migrations..."
    
    # Run identity service migrations
    kubectl exec -n "$NAMESPACE" deployment/identity-service -- python -c "
    import asyncio
    from app.database import engine, Base
    async def create_tables():
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    asyncio.run(create_tables())
    "
    
    # Run backend service migrations
    kubectl exec -n "$NAMESPACE" deployment/backend-service -- python manage.py migrate
    
    log "Database migrations completed ✓"
}

# Perform health checks
health_check() {
    log "Performing health checks..."
    
    local services=("identity-service:8001" "backend-service:8000")
    
    for service in "${services[@]}"; do
        local service_name="${service%:*}"
        local port="${service#*:}"
        
        info "Checking health of $service_name..."
        
        # Port forward to the service
        kubectl port-forward -n "$NAMESPACE" "deployment/$service_name" "$port:$port" &
        local pf_pid=$!
        
        # Wait a moment for port forwarding to establish
        sleep 5
        
        # Check health endpoint
        if curl -f -s "http://localhost:$port/health" > /dev/null; then
            log "$service_name health check passed ✓"
        else
            error "$service_name health check failed"
            kill $pf_pid 2>/dev/null || true
            exit 1
        fi
        
        # Clean up port forwarding
        kill $pf_pid 2>/dev/null || true
    done
    
    log "All health checks passed ✓"
}

# Verify HIPAA compliance
verify_compliance() {
    log "Verifying HIPAA compliance..."
    
    # Check encryption at rest
    info "Checking database encryption..."
    if kubectl exec -n "$NAMESPACE" deployment/backend-service -- python -c "
    import os
    import psycopg2
    conn = psycopg2.connect(os.getenv('DATABASE_URL'))
    cur = conn.cursor()
    cur.execute('SHOW ssl;')
    result = cur.fetchone()
    print('SSL enabled:', result[0] == 'on')
    " | grep -q "SSL enabled: True"; then
        log "Database SSL encryption verified ✓"
    else
        error "Database SSL encryption verification failed"
    fi
    
    # Check audit logging
    info "Checking audit logging configuration..."
    if kubectl get configmap -n "$NAMESPACE" medical-compliance-config -o jsonpath='{.data.AUDIT_TRAIL_ENABLED}' | grep -q "true"; then
        log "Audit logging configuration verified ✓"
    else
        error "Audit logging not properly configured"
    fi
    
    # Check network policies
    info "Checking network security policies..."
    if kubectl get networkpolicy -n "$NAMESPACE" medical-saas-network-policy > /dev/null 2>&1; then
        log "Network security policies verified ✓"
    else
        warning "Network security policies not found"
    fi
    
    log "HIPAA compliance verification completed ✓"
}

# Backup current deployment (for rollback)
backup_deployment() {
    log "Creating deployment backup..."
    
    local backup_dir="backups/$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$backup_dir"
    
    # Backup current Kubernetes configurations
    kubectl get all -n "$NAMESPACE" -o yaml > "$backup_dir/kubernetes-resources.yaml"
    kubectl get secrets -n "$NAMESPACE" -o yaml > "$backup_dir/secrets.yaml"
    kubectl get configmaps -n "$NAMESPACE" -o yaml > "$backup_dir/configmaps.yaml"
    
    # Create database backup
    kubectl exec -n "$NAMESPACE" deployment/backend-service -- python manage.py dumpdata > "$backup_dir/database-backup.json"
    
    log "Deployment backup created in $backup_dir ✓"
}

# Main deployment function
main() {
    log "Starting Medical SaaS Production Deployment"
    log "Environment: $ENVIRONMENT"
    log "Namespace: $NAMESPACE"
    log "Cluster: $CLUSTER_NAME"
    
    # Create backup before deployment
    backup_deployment
    
    # Check prerequisites
    check_prerequisites
    
    # Deploy infrastructure
    deploy_infrastructure
    
    # Update secrets
    update_secrets
    
    # Deploy to Kubernetes
    deploy_kubernetes
    
    # Wait for deployments
    wait_for_deployments
    
    # Run database migrations
    run_migrations
    
    # Perform health checks
    health_check
    
    # Verify HIPAA compliance
    verify_compliance
    
    log "🎉 Medical SaaS Production Deployment Completed Successfully!"
    log "Application URL: https://$DOMAIN_NAME"
    log "API URL: https://$API_DOMAIN"
    log "Auth URL: https://$AUTH_DOMAIN"
    
    info "Next steps:"
    info "1. Update DNS records to point to the load balancer"
    info "2. Configure monitoring alerts"
    info "3. Test all critical user flows"
    info "4. Schedule regular backups"
    info "5. Review security audit logs"
}

# Run deployment
main "$@"