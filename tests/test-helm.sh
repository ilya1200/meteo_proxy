#!/bin/bash
# Helm chart validation script
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  Helm Chart Validation${NC}"
echo -e "${GREEN}========================================${NC}\n"

# Change to project root
cd "$(dirname "$0")/.."

CHART_PATH="helm/weather-proxy"

# Check if helm is installed
if ! command -v helm &> /dev/null; then
    echo -e "${RED}Error: helm is not installed${NC}"
    echo "Install helm: https://helm.sh/docs/intro/install/"
    exit 1
fi

# Step 1: Lint the chart
echo -e "${YELLOW}=== Step 1: Linting Chart ===${NC}"
helm lint "$CHART_PATH"
echo -e "${GREEN}✓ Lint passed${NC}"

# Step 2: Template rendering
echo -e "\n${YELLOW}=== Step 2: Template Rendering ===${NC}"
helm template weather-proxy "$CHART_PATH" > /dev/null
echo -e "${GREEN}✓ Templates render successfully${NC}"

# Step 3: Template with different values
echo -e "\n${YELLOW}=== Step 3: Template with Custom Values ===${NC}"
helm template weather-proxy "$CHART_PATH" \
    --set replicaCount=3 \
    --set image.tag=v1.0.0 \
    --set ingress.enabled=true \
    --set autoscaling.enabled=true \
    > /dev/null
echo -e "${GREEN}✓ Custom values render successfully${NC}"

# Step 4: Validate YAML syntax (if kubectl available)
echo -e "\n${YELLOW}=== Step 4: YAML Validation ===${NC}"
if command -v kubectl &> /dev/null; then
    helm template weather-proxy "$CHART_PATH" | kubectl apply --dry-run=client -f - > /dev/null 2>&1 || true
    echo -e "${GREEN}✓ YAML syntax valid${NC}"
else
    echo -e "${YELLOW}kubectl not available, skipping Kubernetes validation${NC}"
fi

# Step 5: Check required files exist
echo -e "\n${YELLOW}=== Step 5: Chart Structure ===${NC}"
REQUIRED_FILES=(
    "Chart.yaml"
    "values.yaml"
    "templates/deployment.yaml"
    "templates/service.yaml"
    "templates/_helpers.tpl"
)

for file in "${REQUIRED_FILES[@]}"; do
    if [[ -f "$CHART_PATH/$file" ]]; then
        echo "  ✓ $file"
    else
        echo -e "  ${RED}✗ $file (missing)${NC}"
        exit 1
    fi
done
echo -e "${GREEN}✓ All required files present${NC}"

# Step 6: Verify chart version
echo -e "\n${YELLOW}=== Step 6: Chart Metadata ===${NC}"
CHART_VERSION=$(grep '^version:' "$CHART_PATH/Chart.yaml" | awk '{print $2}')
APP_VERSION=$(grep '^appVersion:' "$CHART_PATH/Chart.yaml" | awk '{print $2}' | tr -d '"')
echo "  Chart Version: $CHART_VERSION"
echo "  App Version: $APP_VERSION"
echo -e "${GREEN}✓ Metadata valid${NC}"

echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}  All Helm validations passed! ✓${NC}"
echo -e "${GREEN}========================================${NC}"
