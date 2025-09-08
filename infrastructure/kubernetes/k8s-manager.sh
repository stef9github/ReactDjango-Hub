#!/bin/bash
# Kubernetes management script for ReactDjango Hub Medical SaaS

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

print_status() { echo -e "${GREEN}[K8S]${NC} $1"; }
print_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
print_error() { echo -e "${RED}[ERROR]${NC} $1"; }
print_header() { echo -e "${BLUE}=== $1 ===${NC}"; }

show_usage() {
    cat << EOF
Kubernetes Manager for ReactDjango Hub Medical SaaS

Usage: $0 <command> [options]

Commands:
    deploy              - Deploy all services to Kubernetes
    undeploy            - Remove all services from Kubernetes
    status              - Show deployment status
    logs <service>      - Show logs for a service
    scale <service> <replicas> - Scale a service
    restart <service>   - Restart a service
    migrate             - Run database migrations in cluster
    backup              - Backup database from cluster
    update-images       - Update container images
    create-secrets      - Create required secrets (interactive)

Services: backend, frontend, database, redis

Prerequisites:
    - kubectl configured with cluster access
    - Docker images built and pushed to registry
    - Secrets configured (use create-secrets command)

Examples:
    $0 deploy
    $0 logs backend
    $0 scale backend 5
    $0 migrate
EOF
}

check_prerequisites() {
    print_header "Checking Prerequisites"
    
    # Check kubectl
    if ! command -v kubectl &> /dev/null; then
        print_error "kubectl is not installed or not in PATH"
        exit 1
    fi
    
    # Check cluster connection
    if ! kubectl cluster-info &> /dev/null; then
        print_error "Cannot connect to Kubernetes cluster"
        print_warning "Make sure kubectl is configured: kubectl config view"
        exit 1
    fi
    
    # Check if namespace exists
    if kubectl get namespace medicalhub &> /dev/null; then
        print_status "✅ Namespace 'medicalhub' exists"
    else
        print_warning "Namespace 'medicalhub' does not exist - will create during deployment"
    fi
    
    print_status "✅ Prerequisites check passed"
}

deploy_services() {
    print_header "Deploying ReactDjango Hub to Kubernetes"
    check_prerequisites
    
    cd "$SCRIPT_DIR"
    
    # Deploy using kustomize
    print_status "Applying Kubernetes manifests..."
    kubectl apply -k .
    
    print_status "Waiting for deployments to be ready..."
    kubectl wait --for=condition=available --timeout=300s deployment/backend -n medicalhub
    kubectl wait --for=condition=available --timeout=300s deployment/frontend -n medicalhub
    
    print_status "✅ Deployment completed!"
    show_status
}

undeploy_services() {
    print_header "Removing ReactDjango Hub from Kubernetes"
    
    cd "$SCRIPT_DIR"
    
    print_warning "This will remove all services, data, and secrets!"
    read -p "Are you sure? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_status "Cancelled"
        exit 0
    fi
    
    kubectl delete -k . || true
    
    print_status "✅ Services removed"
}

show_status() {
    print_header "Deployment Status"
    
    print_status "Pods:"
    kubectl get pods -n medicalhub -o wide
    
    echo ""
    print_status "Services:"
    kubectl get services -n medicalhub
    
    echo ""
    print_status "Ingress:"
    kubectl get ingress -n medicalhub
    
    echo ""
    print_status "Persistent Volumes:"
    kubectl get pvc -n medicalhub
}

show_logs() {
    local service=${1:-backend}
    print_header "Logs for $service"
    
    kubectl logs -f deployment/$service -n medicalhub
}

scale_service() {
    local service=${1:-backend}
    local replicas=${2:-3}
    
    print_header "Scaling $service to $replicas replicas"
    
    kubectl scale deployment/$service --replicas=$replicas -n medicalhub
    
    print_status "Waiting for scaling to complete..."
    kubectl wait --for=condition=available --timeout=120s deployment/$service -n medicalhub
    
    print_status "✅ Scaling completed"
}

restart_service() {
    local service=${1:-backend}
    
    print_header "Restarting $service"
    
    kubectl rollout restart deployment/$service -n medicalhub
    kubectl rollout status deployment/$service -n medicalhub
    
    print_status "✅ Restart completed"
}

run_migrations() {
    print_header "Running Database Migrations"
    
    print_status "Creating migration job..."
    kubectl create job --from=deployment/backend migration-$(date +%s) -n medicalhub
    
    # Wait for job completion
    print_status "Waiting for migration to complete..."
    sleep 5
    
    # Show logs
    kubectl logs -f job/migration-$(date +%s) -n medicalhub
}

create_secrets() {
    print_header "Creating Kubernetes Secrets"
    print_warning "This will prompt for sensitive information"
    
    read -s -p "Database Password: " db_password
    echo ""
    read -s -p "Redis Password: " redis_password  
    echo ""
    read -s -p "Django Secret Key (min 50 chars): " secret_key
    echo ""
    
    # Create secrets
    kubectl create secret generic backend-secrets \
        --from-literal=database-password="$db_password" \
        --from-literal=redis-password="$redis_password" \
        --from-literal=secret-key="$secret_key" \
        -n medicalhub --dry-run=client -o yaml | kubectl apply -f -
    
    print_status "✅ Secrets created"
}

update_images() {
    print_header "Updating Container Images"
    
    # Restart deployments to pull latest images
    kubectl rollout restart deployment/backend -n medicalhub
    kubectl rollout restart deployment/frontend -n medicalhub
    
    # Wait for rollouts
    kubectl rollout status deployment/backend -n medicalhub
    kubectl rollout status deployment/frontend -n medicalhub
    
    print_status "✅ Images updated"
}

main() {
    case "${1:-}" in
        deploy)
            deploy_services
            ;;
        undeploy)
            undeploy_services
            ;;
        status)
            show_status
            ;;
        logs)
            show_logs "${2:-backend}"
            ;;
        scale)
            scale_service "${2:-backend}" "${3:-3}"
            ;;
        restart)
            restart_service "${2:-backend}"
            ;;
        migrate)
            run_migrations
            ;;
        create-secrets)
            create_secrets
            ;;
        update-images)
            update_images
            ;;
        *)
            show_usage
            exit 1
            ;;
    esac
}

main "$@"