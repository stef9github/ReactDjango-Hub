#!/bin/bash
# Quick command to show API documentation locations for agents

echo -e "\033[1;32m📚 API Documentation Locations\033[0m"
echo ""

echo -e "\033[1;34m🔗 Shared API Contract:\033[0m"
echo -e "  📄 docs/api/README.md - API contract between agents"
echo ""

echo -e "\033[1;32m🔧 Backend API Documentation:\033[0m"  
echo -e "  📄 backend/docs/api/README.md - Complete API specification"
echo -e "  📄 http://localhost:8000/api/docs/ - Swagger UI (when server running)"
echo -e "  📄 http://localhost:8000/api/schema/ - OpenAPI schema"
echo ""

echo -e "\033[1;35m🎨 Frontend API Integration:\033[0m"
echo -e "  📄 frontend/docs/api/README.md - Integration guide for React"
echo -e "  📄 frontend/src/api/ - TypeScript API client implementation"
echo ""

echo -e "\033[1;36m⚡ Quick Commands:\033[0m"
echo -e "  \033[1;33mBackend Agent:\033[0m"
echo -e "    cd ../ReactDjango-Hub-worktrees/backend-dev"
echo -e "    cat backend/docs/api/README.md"
echo ""
echo -e "  \033[1;33mFrontend Agent:\033[0m"  
echo -e "    cd ../ReactDjango-Hub-worktrees/frontend-dev"
echo -e "    cat frontend/docs/api/README.md"
echo -e "    cat ../../ReactDjango-Hub/backend/docs/api/README.md"
echo ""

# Check if we're in a worktree to provide specific guidance
if [[ "$PWD" == *"backend-dev"* ]]; then
    echo -e "\033[1;32m✅ You're in Backend Agent worktree\033[0m"
    echo -e "  📖 Read backend API docs: \033[1;33mcat backend/docs/api/README.md\033[0m"
elif [[ "$PWD" == *"frontend-dev"* ]]; then
    echo -e "\033[1;35m✅ You're in Frontend Agent worktree\033[0m"
    echo -e "  📖 Read frontend API guide: \033[1;33mcat frontend/docs/api/README.md\033[0m"
    echo -e "  📖 Check backend API spec: \033[1;33mcat ../../ReactDjango-Hub/backend/docs/api/README.md\033[0m"
else
    echo -e "\033[1;36m📍 You're in main repository\033[0m"
    echo -e "  📖 Read API contract: \033[1;33mcat docs/api/README.md\033[0m"
fi