name: "Docker & Archon Setup PRP - Infrastructure Prerequisites"
description: |
  Docker installation and Archon MCP server setup requirements
  for Hills & Hollows LLC DABS Automation project infrastructure

---

## Goal

**Feature Goal**: Complete Docker installation and Archon MCP server deployment to enable advanced project management and AI assistant integration for the DABS automation system.

**Deliverable**: Operational Archon MCP server accessible at http://localhost:3737 with Docker containerized services running all required components.

**Success Definition**: 
- Docker Desktop installed and operational
- Archon services running (UI, API, MCP, Agents)
- Web interface accessible via Playwright automation
- MCP server ready for AI assistant integration
- Knowledge base operational for DABS project management

## User Persona

**Target User**: Development Team & Tessa Brakan (Store Manager)
- **Role**: Project infrastructure setup and ongoing project management
- **Current Pain**: No centralized project management or AI assistant integration
- **Goals**: Streamlined development workflow, centralized documentation, AI-powered project insights

**Use Case**: Infrastructure setup for enhanced development workflow
1. Install Docker → Deploy Archon services
2. Configure environment → Setup knowledge base
3. Import DABS project → Enable AI assistant integration
4. Manage automation phases → Track progress with intelligent insights

**Pain Points Addressed**:
- Fragmented project documentation
- No centralized task management
- Limited AI assistant context
- Lack of development infrastructure

## Why

- **Development Value**: Centralized project management with AI integration
- **Integration**: Connects all project documentation and task management
- **Problems Solved**: Infrastructure gaps preventing advanced development workflow
- **User Impact**: Enables sophisticated project management and AI-powered insights

## What

Complete Docker and Archon infrastructure deployment with integrated project management capabilities.

### Success Criteria

- [ ] **Docker Installation**: Docker Desktop operational with container management
- [ ] **Archon Services**: All 4 services running (UI, Server, MCP, Agents)
- [ ] **Web Interface**: Accessible at http://localhost:3737
- [ ] **MCP Integration**: AI assistants can connect to knowledge base
- [ ] **DABS Project Import**: Automation project imported with PRP
- [ ] **Knowledge Base**: Documentation and code examples searchable

## All Needed Context

### Documentation & References

```yaml
# DOCKER INSTALLATION REQUIREMENTS
- url: https://www.docker.com/products/docker-desktop/
  why: Official Docker Desktop installation for macOS
  critical: Required for Archon containerized services

- file: archon-mcp/docker-compose.yml
  why: Archon service configuration and port mapping
  pattern: 4-service microservices architecture
  gotcha: Requires specific environment variables and Supabase

- file: archon-mcp/README.md
  why: Complete Archon setup instructions and prerequisites
  pattern: Step-by-step installation and configuration
  critical: Environment setup and database migration required
```

### Current Codebase Tree (Docker Components Present)

```bash
archon-mcp/
├── docker-compose.yml               # Main service orchestration
├── Dockerfile.server               # Server service container
├── Dockerfile.mcp                  # MCP service container  
├── Dockerfile.agents               # Agents service container
├── archon-ui-main/
│   └── Dockerfile                  # Frontend UI container
├── python/                         # Python services source
├── migration/
│   ├── complete_setup.sql          # Database initialization
│   └── RESET_DB.sql               # Database reset script
└── docs/                          # Documentation service
```

### Required Infrastructure Setup

```bash
# Current Status Analysis:
❌ Docker Desktop: Not installed (command not found)
❌ Archon Services: Not running (connection refused)
✅ Homebrew: Available for package management
✅ Python: Available for scripting
✅ Playwright: Available for web testing
✅ Project Files: All Archon files present and ready
```

## Implementation Blueprint

### Data Models and Structure ✅ READY

Infrastructure components are prepared:
- Docker compose configuration with 4 services
- Environment variable templates
- Database migration scripts
- Service health checks and networking

### Implementation Tasks (Ordered by Dependencies)

```yaml
Task 1: INSTALL Docker Desktop
  - DOWNLOAD: Docker Desktop for macOS from official website
  - INSTALL: Run installer and complete setup wizard
  - VERIFY: docker --version and docker-compose --version commands work
  - START: Docker Desktop application and ensure running

Task 2: CONFIGURE Supabase Database
  - CREATE: Free Supabase account at https://supabase.com
  - SETUP: New project with PostgreSQL + PGVector
  - OBTAIN: Project URL and service key credentials
  - MIGRATE: Run complete_setup.sql in Supabase SQL Editor

Task 3: SETUP Environment Configuration
  - CREATE: .env file from template in archon-mcp directory
  - CONFIGURE: Supabase credentials (URL, service key)
  - OPTIONAL: OpenAI API key for enhanced features
  - VALIDATE: All required environment variables set

Task 4: DEPLOY Archon Services
  - NAVIGATE: cd archon-mcp directory
  - BUILD: docker-compose up --build -d (start all services)
  - WAIT: 2-3 minutes for service initialization
  - VALIDATE: Health checks pass for all 4 services

Task 5: VERIFY Web Interface Access
  - ACCESS: http://localhost:3737 (Archon UI)
  - TEST: Knowledge base, projects, settings pages
  - CONFIGURE: LLM provider and API keys in settings
  - VALIDATE: MCP server connectivity at http://localhost:8051

Task 6: IMPORT DABS Project
  - CREATE: New project via Archon web interface
  - UPLOAD: DABS_Automation_Complete_PRP.md document
  - CONFIGURE: Project settings and task management
  - VALIDATE: MCP tools accessible to AI assistants
```

### Service Architecture & Ports

```yaml
ARCHON MICROSERVICES CONFIGURATION:
  archon-ui:     Port 3737  (Web Interface)
  archon-server: Port 8181  (Core API + Socket.IO)
  archon-mcp:    Port 8051  (MCP Protocol Interface)
  archon-agents: Port 8052  (AI Operations)

DOCKER SERVICES HEALTH CHECKS:
  - Automatic health monitoring
  - Service restart on failure
  - Inter-service communication validation
  - Resource usage monitoring
```

## Validation Loop

### Level 1: Docker Installation Validation

```bash
# Verify Docker components
docker --version                    # Should show Docker version
docker-compose --version           # Should show compose version
docker info                        # Should show Docker daemon info

# Expected: All Docker commands functional
```

### Level 2: Archon Services Validation

```bash
# Start services and validate
cd archon-mcp
docker-compose up --build -d

# Check service status
docker-compose ps                   # All services should be "Up"
docker-compose logs archon-server  # Check for startup errors
docker-compose logs archon-mcp     # Validate MCP server start

# Expected: All 4 services running without errors
```

### Level 3: Web Interface Validation

```bash
# Test web accessibility
curl -f http://localhost:3737 || echo "UI not accessible"
curl -f http://localhost:8181/health || echo "API not healthy"
curl -f http://localhost:8051/health || echo "MCP not healthy"

# Playwright testing
python3 scripts/playwright_archon_test.py

# Expected: All services respond correctly, Playwright succeeds
```

### Level 4: MCP Integration Validation

```bash
# Test MCP tools functionality
# This would test the 10 MCP commands:
# - get_available_sources()
# - perform_rag_query()
# - search_code_examples()
# - manage_project()
# - manage_task()
# - manage_document()
# - manage_versions()
# - get_project_features()
# - get_health_status()
# - manage_session()

# Expected: All MCP tools respond correctly
```

## Installation Steps - Detailed Task List

### ✅ DOCKER INSTALLATION CHECKLIST

```bash
# Step 1: Download Docker Desktop
open https://www.docker.com/products/docker-desktop/

# Step 2: Install Docker Desktop
# - Run downloaded installer
# - Follow setup wizard
# - Grant necessary permissions
# - Start Docker Desktop application

# Step 3: Verify Installation
docker --version                   # Should show version
docker info                       # Should show daemon running
docker run hello-world            # Should download and run test container

# Step 4: Configure Docker (Optional)
# - Increase memory allocation (8GB+ recommended)
# - Enable BuildKit for faster builds
# - Configure resource limits
```

### ✅ ARCHON SETUP CHECKLIST

```bash
# Step 1: Environment Setup
cd archon-mcp
cp .env.example .env              # Create environment file

# Step 2: Configure Supabase
# Edit .env file with:
# SUPABASE_URL=https://your-project.supabase.co
# SUPABASE_SERVICE_KEY=your-service-key-here

# Step 3: Database Migration
# In Supabase SQL Editor, execute:
# - migration/complete_setup.sql

# Step 4: Start Services
docker-compose up --build -d      # Build and start all services

# Step 5: Verify Deployment
docker-compose ps                 # Check all services are "Up"
curl http://localhost:3737        # Test web interface
curl http://localhost:8181/health # Test API health
```

## Integration Points

### ✅ ENVIRONMENT CONFIGURATION

```yaml
REQUIRED ENVIRONMENT VARIABLES:
  SUPABASE_URL: Database connection URL
  SUPABASE_SERVICE_KEY: Database authentication
  OPENAI_API_KEY: Optional for enhanced AI features
  ARCHON_UI_PORT: Default 3737
  ARCHON_SERVER_PORT: Default 8181
  ARCHON_MCP_PORT: Default 8051
  ARCHON_AGENTS_PORT: Default 8052

DOCKER CONFIGURATION:
  Memory: 8GB+ recommended
  Storage: 20GB+ available space
  Network: Ports 3737, 8051, 8181, 8052 accessible
```

### ✅ SERVICE DEPENDENCIES

```yaml
STARTUP ORDER:
  1. Database (Supabase) - Must be configured first
  2. Server Service - Core API and business logic
  3. MCP Service - Protocol interface for AI clients
  4. Agents Service - AI operations and processing
  5. UI Service - Web interface and dashboard

HEALTH CHECKS:
  - All services have automatic health monitoring
  - Failed services restart automatically
  - Service discovery validates inter-service communication
```

## Final Validation Checklist

### Infrastructure Validation ✅ READY FOR TESTING

- [ ] **Docker Desktop**: Installed and running
- [ ] **Service Ports**: 3737, 8051, 8181, 8052 accessible
- [ ] **Database**: Supabase configured and migrated
- [ ] **Environment**: All variables configured in .env

### Service Validation ✅ READY FOR TESTING

- [ ] **Web Interface**: http://localhost:3737 accessible
- [ ] **API Health**: http://localhost:8181/health responds
- [ ] **MCP Server**: http://localhost:8051/health responds
- [ ] **All Services**: docker-compose ps shows "Up" status

### Integration Validation ✅ READY FOR TESTING

- [ ] **Playwright Access**: Web interface automation working
- [ ] **MCP Tools**: All 10 tools functional
- [ ] **Knowledge Base**: Document upload and search working
- [ ] **Project Management**: Task creation and tracking operational

---

## Current Status Assessment

### ❌ DOCKER NOT INSTALLED (Primary Blocker)
```
Current Status:
  Docker Command: ❌ Not found
  Docker Compose: ❌ Not found
  Docker Desktop: ❌ Not installed in /Applications/
  
Required Actions:
  1. Download Docker Desktop for macOS
  2. Install and start Docker Desktop
  3. Verify installation with docker --version
  4. Proceed with Archon deployment
```

### ✅ INFRASTRUCTURE READY (Supporting Components)
```
Ready Components:
  Homebrew: ✅ Available for additional packages
  Python: ✅ Available for scripting
  Playwright: ✅ Available for web testing
  Archon Files: ✅ Complete docker-compose.yml present
  Project Space: ✅ All configuration files ready
```

---

## ✅ PRP CONCLUSION: DOCKER SETUP REQUIRED

**INFRASTRUCTURE STATUS**: ❌ **Docker Installation Required**

**TASK LIST STATUS**: ✅ **Complete Setup Guide Provided**

**DEPLOYMENT READINESS**: ⚠️ **Pending Docker Installation**

This PRP provides the complete task list and requirements for Docker installation and Archon setup. Once Docker is installed, the Archon services can be deployed and the DABS automation project can benefit from advanced project management capabilities.
