#!/bin/bash
# ============================================
# KAOS WSL Health Check
# ============================================

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

echo ""
echo -e "${CYAN}========================================${NC}"
echo -e "${CYAN}   KAOS Health Check${NC}"
echo -e "${CYAN}========================================${NC}"
echo ""

# Verificar Docker
echo -e "${YELLOW}[Docker]${NC}"
if systemctl is-active --quiet docker; then
    echo -e "  Daemon:   ${GREEN}Activo${NC}"
else
    echo -e "  Daemon:   ${RED}Inactivo${NC}"
fi

# Contenedores
echo ""
echo -e "${YELLOW}[Contenedores]${NC}"
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" --filter "label=com.docker.compose.project" 2>/dev/null

# Endpoints
echo ""
echo -e "${YELLOW}[Endpoints]${NC}"

check_endpoint() {
    local name=$1
    local url=$2
    
    if curl -s -o /dev/null -w "%{http_code}" --max-time 3 "$url" | grep -q "200"; then
        echo -e "  ${GREEN}OK${NC}  $name -> $url"
    else
        echo -e "  ${RED}OFF${NC} $name -> $url"
    fi
}

check_endpoint "Langfuse" "http://127.0.0.1:3001"
check_endpoint "SearXNG" "http://127.0.0.1:8888"
check_endpoint "Crawl4AI" "http://127.0.0.1:11235/health"
check_endpoint "Kroki" "http://127.0.0.1:8000/health"
check_endpoint "DeerFlow" "http://127.0.0.1:8001"

# Recursos
echo ""
echo -e "${YELLOW}[Recursos Docker]${NC}"
docker system df --format "table {{.Type}}\t{{.Size}}\t{{.Reclaimable}}" 2>/dev/null

echo ""
echo -e "${CYAN}========================================${NC}"
echo ""
