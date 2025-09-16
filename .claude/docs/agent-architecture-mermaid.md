# Agent Architecture Visual Guide for ReactDjango-Hub

## Overview

This document provides a comprehensive visual representation of the agent architecture for building the ReactDjango-Hub SaaS application. The system uses specialized Claude Code agents, each responsible for specific domains, with strict boundaries to maintain clean separation of concerns.

## 1. Overall Agent Hierarchy and Relationships

```mermaid
graph TB
    subgraph "Leadership & Strategy"
        TL[🎯 Technical Lead<br/>Architecture & Research]
        SPM[🏥 Surgical Product Manager<br/>Medical Market Strategy]
        PPM[🏛️ Public Procurement PM<br/>GovTech Strategy]
        PLM[📊 Platform Product Manager<br/>Unified Platform Strategy]
    end
    
    subgraph "Quality & Compliance"
        SEC[🔒 Security & Compliance<br/>Audits & Standards]
        REV[👀 Code Reviewer<br/>Quality Assurance]
    end
    
    subgraph "Infrastructure & Coordination"
        INFRA[🚀 Infrastructure<br/>Docker/K8s/Deployment]
        COORD[🎯 Services Coordinator<br/>API Gateway & Integration]
    end
    
    subgraph "Core Services"
        BE[🔧 Django Backend<br/>Business Logic]
        FE[🎨 React Frontend<br/>User Interface]
    end
    
    subgraph "Microservices"
        ID[🔐 Identity Service<br/>Auth & Users]
        COMM[📧 Communication<br/>Notifications]
        CONT[📝 Content Service<br/>Documents]
        WF[🧠 Workflow Intelligence<br/>Automation & AI]
    end
    
    %% Leadership relationships
    TL -->|Defines Architecture| INFRA
    TL -->|Sets Standards| COORD
    TL -->|Guides Development| BE
    TL -->|Guides Development| FE
    
    SPM -->|Product Requirements| FE
    PPM -->|Product Requirements| FE
    PLM -->|Platform Strategy| COORD
    
    %% Quality relationships
    SEC -.->|Security Review| BE
    SEC -.->|Security Review| FE
    SEC -.->|Security Review| ID
    SEC -.->|Compliance Check| COMM
    SEC -.->|Compliance Check| CONT
    SEC -.->|Compliance Check| WF
    
    REV -.->|Code Review| BE
    REV -.->|Code Review| FE
    REV -.->|Code Review| ID
    REV -.->|Code Review| COMM
    REV -.->|Code Review| CONT
    REV -.->|Code Review| WF
    
    %% Infrastructure relationships
    INFRA -->|Containerizes| BE
    INFRA -->|Containerizes| FE
    INFRA -->|Containerizes| ID
    INFRA -->|Containerizes| COMM
    INFRA -->|Containerizes| CONT
    INFRA -->|Containerizes| WF
    
    %% Coordination relationships
    COORD -->|API Contracts| BE
    COORD -->|API Contracts| ID
    COORD -->|API Contracts| COMM
    COORD -->|API Contracts| CONT
    COORD -->|API Contracts| WF
    COORD -->|Aggregates APIs| FE
    
    %% Service dependencies
    FE -->|Consumes APIs| BE
    BE -->|Uses Auth| ID
    BE -->|Sends Notifications| COMM
    BE -->|Manages Content| CONT
    BE -->|Triggers Workflows| WF
    
    style TL fill:#f9f,stroke:#333,stroke-width:4px
    style INFRA fill:#bbf,stroke:#333,stroke-width:2px
    style COORD fill:#bbf,stroke:#333,stroke-width:2px
    style SEC fill:#fbb,stroke:#333,stroke-width:2px
    style REV fill:#fbb,stroke:#333,stroke-width:2px
```

## 2. Service Boundaries and Constraints

```mermaid
graph LR
    subgraph "Django Backend Domain"
        BE_CODE[backend/<br/>- apps/<br/>- config/<br/>- tests/]
        BE_DB[(PostgreSQL<br/>django_backend_db)]
        BE_API[REST APIs<br/>Django Ninja<br/>Port: 8000]
    end
    
    subgraph "React Frontend Domain"
        FE_CODE[frontend/<br/>- src/<br/>- components/<br/>- pages/]
        FE_BUILD[Build Output<br/>- dist/<br/>- static/]
        FE_UI[UI<br/>React + Vite<br/>Port: 3000]
    end
    
    subgraph "Identity Service Domain"
        ID_CODE[services/<br/>identity-service/<br/>- main.py<br/>- tests/]
        ID_DB[(PostgreSQL<br/>identity_service_db)]
        ID_API[Auth APIs<br/>FastAPI<br/>Port: 8001]
    end
    
    subgraph "Communication Service Domain"
        COMM_CODE[services/<br/>communication-service/<br/>- main.py<br/>- tests/]
        COMM_DB[(PostgreSQL<br/>communication_db)]
        COMM_API[Notification APIs<br/>FastAPI<br/>Port: 8002]
    end
    
    subgraph "Content Service Domain"
        CONT_CODE[services/<br/>content-service/<br/>- main.py<br/>- tests/]
        CONT_DB[(PostgreSQL<br/>content_db)]
        CONT_API[Document APIs<br/>FastAPI<br/>Port: 8003]
    end
    
    subgraph "Workflow Service Domain"
        WF_CODE[services/<br/>workflow-service/<br/>- main.py<br/>- tests/]
        WF_DB[(PostgreSQL<br/>workflow_db)]
        WF_API[Automation APIs<br/>FastAPI<br/>Port: 8004]
    end
    
    subgraph "Infrastructure Domain"
        INFRA_CODE[infrastructure/<br/>- docker/<br/>- kubernetes/<br/>- scripts/]
        KONG[Kong<br/>API Gateway<br/>Port: 8000]
    end
    
    %% Boundary rules
    BE_CODE -.->|Cannot modify| ID_CODE
    BE_CODE -.->|Cannot modify| COMM_CODE
    BE_CODE -.->|Cannot modify| CONT_CODE
    BE_CODE -.->|Cannot modify| WF_CODE
    BE_CODE -.->|Cannot access| ID_DB
    BE_CODE -.->|Cannot access| COMM_DB
    BE_CODE -.->|Cannot access| CONT_DB
    BE_CODE -.->|Cannot access| WF_DB
    
    FE_CODE -.->|Cannot modify| BE_CODE
    FE_CODE -.->|Cannot modify| ID_CODE
    FE_CODE -.->|Cannot modify| COMM_CODE
    
    ID_CODE -.->|Cannot modify| BE_CODE
    ID_CODE -.->|Cannot modify| FE_CODE
    ID_CODE -.->|Cannot access| BE_DB
    
    style BE_CODE fill:#e1f5fe
    style FE_CODE fill:#f3e5f5
    style ID_CODE fill:#fff3e0
    style COMM_CODE fill:#e8f5e9
    style CONT_CODE fill:#fce4ec
    style WF_CODE fill:#fff8e1
    style INFRA_CODE fill:#e3f2fd
```

## 3. Communication Flow Patterns

```mermaid
sequenceDiagram
    participant User
    participant Frontend
    participant Kong as Kong Gateway
    participant Backend
    participant Identity as Identity Service
    participant Comm as Communication
    participant Content as Content Service
    participant Workflow as Workflow Service
    
    User->>Frontend: User Action
    Frontend->>Kong: API Request
    Kong->>Kong: Route & Auth Check
    
    alt Authentication Required
        Kong->>Identity: Validate JWT
        Identity-->>Kong: Token Valid/Invalid
    end
    
    alt Business Logic Request
        Kong->>Backend: Forward Request
        Backend->>Identity: Get User Context
        Identity-->>Backend: User Details
        Backend->>Content: Get Documents
        Content-->>Backend: Document Data
        Backend->>Workflow: Trigger Process
        Workflow-->>Backend: Process Started
        Backend->>Comm: Send Notification
        Comm-->>Backend: Notification Queued
        Backend-->>Kong: Response
    end
    
    alt Direct Service Request
        Kong->>Content: Direct File Upload
        Content-->>Kong: Upload Complete
    end
    
    Kong-->>Frontend: API Response
    Frontend-->>User: Update UI
    
    Note over Kong: All inter-service communication<br/>goes through API Gateway
    Note over Backend: Aggregates data from<br/>multiple services
    Note over Identity: Single source of truth<br/>for authentication
```

## 4. Development Workflow Using Agents

```mermaid
graph TD
    subgraph "Development Process"
        START[Start Development Task]
        ANALYZE[Analyze Requirements]
        SELECT[Select Appropriate Agent]
        
        START --> ANALYZE
        ANALYZE --> SELECT
        
        SELECT -->|Architecture Change| TL_WORK[Technical Lead Agent<br/>Create ADR]
        SELECT -->|New Feature| FE_BE_WORK{Frontend or Backend?}
        SELECT -->|Security Issue| SEC_WORK[Security Agent<br/>Audit & Fix]
        SELECT -->|Infrastructure| INFRA_WORK[Infrastructure Agent<br/>Update Configs]
        SELECT -->|Service Integration| COORD_WORK[Coordinator Agent<br/>Define Contracts]
        
        FE_BE_WORK -->|UI Component| FE_DEV[Frontend Agent<br/>Implement UI]
        FE_BE_WORK -->|Business Logic| BE_DEV[Backend Agent<br/>Implement API]
        FE_BE_WORK -->|Auth Feature| ID_DEV[Identity Agent<br/>Update Auth]
        FE_BE_WORK -->|Notification| COMM_DEV[Communication Agent<br/>Add Notification]
        FE_BE_WORK -->|Document Feature| CONT_DEV[Content Agent<br/>File Management]
        FE_BE_WORK -->|Automation| WF_DEV[Workflow Agent<br/>Create Workflow]
        
        TL_WORK --> REVIEW[Code Review Agent]
        FE_DEV --> REVIEW
        BE_DEV --> REVIEW
        ID_DEV --> REVIEW
        COMM_DEV --> REVIEW
        CONT_DEV --> REVIEW
        WF_DEV --> REVIEW
        SEC_WORK --> REVIEW
        INFRA_WORK --> REVIEW
        COORD_WORK --> REVIEW
        
        REVIEW --> TEST{Tests Pass?}
        TEST -->|No| FIX[Fix Issues]
        FIX --> SELECT
        TEST -->|Yes| INTEGRATE[Integration Testing]
        
        INTEGRATE --> COORD_TEST[Coordinator Agent<br/>Test Integration]
        COORD_TEST --> DEPLOY{Ready to Deploy?}
        
        DEPLOY -->|No| FIX
        DEPLOY -->|Yes| INFRA_DEPLOY[Infrastructure Agent<br/>Deploy Changes]
        
        INFRA_DEPLOY --> COMPLETE[Task Complete]
    end
    
    style START fill:#90EE90
    style COMPLETE fill:#90EE90
    style REVIEW fill:#FFB6C1
    style TEST fill:#FFD700
    style DEPLOY fill:#FFD700
```

## 5. Agent Decision Tree

```mermaid
graph TD
    Q1{What needs to be done?}
    
    Q1 -->|Architecture Decision| TL[Use Technical Lead Agent]
    Q1 -->|Product Strategy| PM{Which Product?}
    Q1 -->|Code Implementation| Q2{Which Layer?}
    Q1 -->|Quality Check| QC{What Type?}
    Q1 -->|Deployment| INFRA[Use Infrastructure Agent]
    Q1 -->|Integration| COORD[Use Coordinator Agent]
    
    PM -->|Medical SaaS| SPM[Use Surgical PM Agent]
    PM -->|GovTech| PPM[Use Public Procurement PM Agent]
    PM -->|Platform| PLM[Use Platform PM Agent]
    
    Q2 -->|User Interface| FE[Use Frontend Agent]
    Q2 -->|Business Logic| BE[Use Backend Agent]
    Q2 -->|Authentication| ID[Use Identity Agent]
    Q2 -->|Notifications| COMM[Use Communication Agent]
    Q2 -->|Documents| CONT[Use Content Agent]
    Q2 -->|Automation| WF[Use Workflow Agent]
    
    QC -->|Security| SEC[Use Security Agent]
    QC -->|Code Quality| REV[Use Code Review Agent]
    
    %% Add specific commands
    TL -->|Command| TL_CMD[make architecture-review]
    FE -->|Command| FE_CMD[npm run dev]
    BE -->|Command| BE_CMD[python manage.py runserver]
    ID -->|Command| ID_CMD[python main.py]
    COMM -->|Command| COMM_CMD[python main.py]
    CONT -->|Command| CONT_CMD[python main.py]
    WF -->|Command| WF_CMD[python main.py]
    INFRA -->|Command| INFRA_CMD[docker-compose up --build]
    COORD -->|Command| COORD_CMD[pytest services/tests/integration/]
    SEC -->|Command| SEC_CMD[bandit -r .]
    REV -->|Command| REV_CMD[pytest --cov]
    
    style Q1 fill:#f9f
    style Q2 fill:#bbf
    style QC fill:#fbb
    style PM fill:#fbf
```

## 6. Inter-Agent Communication Matrix

```mermaid
graph TB
    subgraph "Communication Matrix"
        subgraph "Can Directly Modify"
            BE_OWN[Backend → backend/]
            FE_OWN[Frontend → frontend/]
            ID_OWN[Identity → identity-service/]
            COMM_OWN[Communication → communication-service/]
            CONT_OWN[Content → content-service/]
            WF_OWN[Workflow → workflow-service/]
            INFRA_OWN[Infrastructure → infrastructure/]
        end
        
        subgraph "Can Request Changes Via"
            BE_REQ[Backend → Coordinator for API changes]
            FE_REQ[Frontend → Coordinator for API integration]
            ID_REQ[Identity → Coordinator for contract updates]
            SERVICE_REQ[Services → Infrastructure for deployment]
            ALL_REQ[All → Technical Lead for architecture]
        end
        
        subgraph "Can Review/Audit"
            SEC_REVIEW[Security → All services]
            REV_REVIEW[Code Review → All code]
            TL_REVIEW[Tech Lead → All architecture]
        end
        
        subgraph "Cannot Access"
            NO_DB[Services ✗ Other service DBs]
            NO_CODE[Services ✗ Other service code]
            NO_INFRA[Services ✗ Infrastructure configs]
        end
    end
    
    style BE_OWN fill:#e1f5fe
    style FE_OWN fill:#f3e5f5
    style ID_OWN fill:#fff3e0
    style COMM_OWN fill:#e8f5e9
    style CONT_OWN fill:#fce4ec
    style WF_OWN fill:#fff8e1
    style INFRA_OWN fill:#e3f2fd
    style NO_DB fill:#ffcccc
    style NO_CODE fill:#ffcccc
    style NO_INFRA fill:#ffcccc
```

## 7. API Contract Management Flow

```mermaid
graph LR
    subgraph "API Contract Lifecycle"
        DESIGN[API Design<br/>OpenAPI Spec]
        IMPLEMENT[Service Implementation]
        TEST[Contract Testing]
        PUBLISH[Publish to Gateway]
        CONSUME[Frontend/Service Consumption]
        
        DESIGN -->|Service Agent| IMPLEMENT
        IMPLEMENT -->|Coordinator Agent| TEST
        TEST -->|Infrastructure Agent| PUBLISH
        PUBLISH -->|Frontend/Service Agents| CONSUME
        CONSUME -->|Feedback| DESIGN
    end
    
    subgraph "Responsible Agents"
        SA[Service Agents<br/>Define & Implement]
        CA[Coordinator Agent<br/>Validate & Test]
        IA[Infrastructure Agent<br/>Deploy & Route]
        FA[Frontend Agent<br/>Consume & Integrate]
    end
    
    SA --> DESIGN
    SA --> IMPLEMENT
    CA --> TEST
    IA --> PUBLISH
    FA --> CONSUME
    
    style DESIGN fill:#ffd700
    style TEST fill:#90ee90
    style PUBLISH fill:#87ceeb
```

## 8. Development Environment State Machine

```mermaid
stateDiagram-v2
    [*] --> LocalDevelopment
    
    LocalDevelopment --> ServiceDevelopment: Start Service Work
    ServiceDevelopment --> UnitTesting: Write Tests
    UnitTesting --> ServiceDevelopment: Tests Fail
    UnitTesting --> IntegrationTesting: Tests Pass
    
    IntegrationTesting --> APIContractValidation: Test Integration
    APIContractValidation --> IntegrationTesting: Contract Invalid
    APIContractValidation --> CodeReview: Contract Valid
    
    CodeReview --> ServiceDevelopment: Changes Requested
    CodeReview --> SecurityReview: Code Approved
    
    SecurityReview --> ServiceDevelopment: Security Issues
    SecurityReview --> ReadyForDeployment: Security Passed
    
    ReadyForDeployment --> ContainerBuild: Build Containers
    ContainerBuild --> DeploymentTesting: Images Built
    
    DeploymentTesting --> ReadyForDeployment: Deploy Failed
    DeploymentTesting --> Production: Deploy Success
    
    Production --> Monitoring: Active
    Monitoring --> LocalDevelopment: New Feature Request
    
    note right of LocalDevelopment: Local-first development<br/>per ADR-010
    note right of ServiceDevelopment: Each service agent<br/>works independently
    note right of IntegrationTesting: Coordinator agent<br/>validates integration
    note right of ContainerBuild: Infrastructure agent<br/>manages deployment
    note right of Production: Future state when<br/>platform matures
```

## 9. Error Handling and Escalation

```mermaid
graph TD
    ERROR[Error Detected]
    
    ERROR --> CLASSIFY{Error Type}
    
    CLASSIFY -->|Service Logic| SERVICE_AGENT[Service Agent<br/>Fix in own domain]
    CLASSIFY -->|Integration| COORD_AGENT[Coordinator Agent<br/>Fix API contracts]
    CLASSIFY -->|Security| SEC_AGENT[Security Agent<br/>Patch vulnerability]
    CLASSIFY -->|Infrastructure| INFRA_AGENT[Infrastructure Agent<br/>Fix deployment]
    CLASSIFY -->|Architecture| TL_AGENT[Technical Lead<br/>Design solution]
    
    SERVICE_AGENT --> RESOLVED{Resolved?}
    COORD_AGENT --> RESOLVED
    SEC_AGENT --> RESOLVED
    INFRA_AGENT --> RESOLVED
    TL_AGENT --> RESOLVED
    
    RESOLVED -->|No| ESCALATE[Escalate to Tech Lead]
    RESOLVED -->|Yes| COMPLETE[Issue Resolved]
    
    ESCALATE --> REVIEW_ARCH[Review Architecture]
    REVIEW_ARCH --> NEW_ADR[Create ADR]
    NEW_ADR --> IMPLEMENT[Implement Solution]
    IMPLEMENT --> COMPLETE
    
    style ERROR fill:#ff6b6b
    style RESOLVED fill:#ffd700
    style COMPLETE fill:#90ee90
    style ESCALATE fill:#ffa500
```

## 10. Best Practices Summary

### Agent Selection Guidelines

| Task Type | Primary Agent | Supporting Agents |
|-----------|---------------|-------------------|
| New UI Component | Frontend | Coordinator (for API) |
| New API Endpoint | Backend/Service | Coordinator (contracts) |
| Authentication Feature | Identity | Security (review) |
| Deployment Issue | Infrastructure | Coordinator (testing) |
| Performance Problem | Technical Lead | Service agents (implement) |
| Security Vulnerability | Security | Service agents (fix) |
| API Integration | Coordinator | Service agents (implement) |
| Architecture Decision | Technical Lead | All agents (feedback) |

### Communication Patterns

1. **Direct Modification**: Agents only modify their own service code
2. **API Communication**: All inter-service communication through APIs
3. **Contract-First**: Define API contracts before implementation
4. **Review Process**: All changes go through code review
5. **Security Scanning**: Automatic security checks on all code

### Boundary Enforcement

```mermaid
graph LR
    subgraph "Allowed"
        A1[Agent modifies own service]
        A2[Agent creates own tests]
        A3[Agent updates own docs]
        A4[Agent defines own APIs]
    end
    
    subgraph "Not Allowed"
        NA1[Agent modifies other services]
        NA2[Agent accesses other DBs]
        NA3[Agent changes infrastructure]
        NA4[Agent bypasses API Gateway]
    end
    
    subgraph "Request Through"
        R1[Coordinator for integration]
        R2[Infrastructure for deployment]
        R3[Tech Lead for architecture]
        R4[Security for compliance]
    end
    
    A1 -.->|If needed| R1
    A4 -.->|For deployment| R2
    A1 -.->|For design| R3
    A1 -.->|For audit| R4
    
    style A1 fill:#90ee90
    style A2 fill:#90ee90
    style A3 fill:#90ee90
    style A4 fill:#90ee90
    style NA1 fill:#ffcccc
    style NA2 fill:#ffcccc
    style NA3 fill:#ffcccc
    style NA4 fill:#ffcccc
```

## Agent Activation Command

To use any agent in development:

```bash
# Launch agent with unified launcher
./.claude/launch-agent.sh <agent-name>

# Examples:
./.claude/launch-agent.sh backend      # Django development
./.claude/launch-agent.sh frontend     # React development
./.claude/launch-agent.sh identity     # Identity service
./.claude/launch-agent.sh coordinator  # API integration
./.claude/launch-agent.sh techlead    # Architecture decisions
```

## Conclusion

This agent architecture ensures:

1. **Clean Separation**: Each agent has clear boundaries and responsibilities
2. **Scalability**: New services can be added without affecting existing ones
3. **Quality**: Multiple review layers ensure code quality and security
4. **Flexibility**: Agents can work independently while maintaining integration
5. **Traceability**: Clear communication patterns and audit trails

The system is designed to support both local-first development (current strategy per ADR-010) and future production deployment with containerization when the platform matures.