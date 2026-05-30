#!/bin/bash
# ============================================
# KAOS WSL Service Manager
# Usage: ./start-services.sh [--all]
# ============================================

KAOS_ROOT="/mnt/c/Users/LeonX/Documents/KAOS"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

ALL_SERVICES=false
if [[ "$1" == "--all" ]]; then
    ALL_SERVICES=true
fi

echo ""
echo -e "${CYAN}========================================${NC}"
echo -e "${CYAN}   KAOS WSL Service Manager${NC}"
echo -e "${CYAN}========================================${NC}"
echo ""

# Check Docker
echo -e "${YELLOW}[1/3] Verificando Docker...${NC}"
if ! systemctl is-active --quiet docker 2>/dev/null; then
    echo "      Iniciando Docker..."
    if ! sudo systemctl start docker 2>/dev/null; then
        echo -e "      ${RED}ERROR: No se pudo iniciar Docker${NC}"
        exit 1
    fi
    sleep 2
fi
echo -e "      ${GREEN}Docker OK${NC}"

# Check docker compose
echo -e "${YELLOW}[2/3] Verificando docker compose...${NC}"
if ! docker compose version > /dev/null 2>&1; then
    echo -e "      ${RED}ERROR: docker compose no disponible${NC}"
    exit 1
fi
echo -e "      ${GREEN}docker compose OK${NC}"

# Start services
echo -e "${YELLOW}[3/3] Levantando servicios...${NC}"

COMPOSE_FILE="$KAOS_ROOT/docker-compose.yml"

if [ "$ALL_SERVICES" = true ]; then
    PROFILES=("core" "langfuse" "agno-db" "sandbox")
    echo -e "      ${CYAN}Perfil: full (todos los servicios)${NC}"
else
    PROFILES=("core")
    echo -e "      ${CYAN}Perfil: core (SearXNG + Crawl4AI)${NC}"
fi

PROFILE_ARGS=()
for p in "${PROFILES[@]}"; do
    PROFILE_ARGS+=("--profile" "$p")
done

echo -n "      -> docker compose up -d..."
if cd "$KAOS_ROOT" && docker compose -f "$COMPOSE_FILE" up -d "${PROFILE_ARGS[@]}" 2>&1; then
    echo -e " ${GREEN}OK${NC}"
else
    echo -e " ${RED}ERROR${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}   Servicios iniciados${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Endpoints:"
echo "  - SearXNG:     http://localhost:8888"
echo "  - Crawl4AI:    http://localhost:11235"
if [ "$ALL_SERVICES" = true ]; then
    echo "  - Langfuse:    http://localhost:3000"
fi
echo ""
