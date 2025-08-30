#!/usr/bin/env bash
# Environment switcher script for Event Booking API

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to show usage
show_usage() {
    echo -e "${BLUE}Event Booking API Environment Switcher${NC}"
    echo ""
    echo "Usage: $0 [development|production|check]"
    echo ""
    echo "Commands:"
    echo "  development  - Set environment to development mode"
    echo "  production   - Set environment to production mode"
    echo "  check        - Check current environment settings"
    echo ""
    echo "Examples:"
    echo "  $0 development"
    echo "  $0 production"
    echo "  $0 check"
}

# Function to set development environment
set_development() {
    echo -e "${GREEN}Setting environment to DEVELOPMENT...${NC}"
    
    # Create .env file if it doesn't exist
    if [ ! -f .env ]; then
        echo "Creating .env file from template..."
        cp env_template.txt .env
        echo -e "${YELLOW}Please edit .env file with your local settings${NC}"
    fi
    
    # Set environment variables
    export ENVIRONMENT=development
    export DEBUG=true
    
    echo -e "${GREEN}Environment set to DEVELOPMENT${NC}"
    echo "You can now run: python manage.py runserver"
}

# Function to set production environment
set_production() {
    echo -e "${GREEN}Setting environment to PRODUCTION...${NC}"
    
    # Set environment variables
    export ENVIRONMENT=production
    export DEBUG=false
    
    echo -e "${GREEN}Environment set to PRODUCTION${NC}"
    echo "Ready for deployment!"
}

# Function to check current environment
check_environment() {
    echo -e "${BLUE}Current Environment Settings:${NC}"
    echo ""
    
    if [ -f .env ]; then
        echo -e "${GREEN}✓ .env file exists${NC}"
        echo "Environment variables from .env:"
        grep -E "^(ENVIRONMENT|DEBUG)=" .env || echo "  (not set in .env)"
    else
        echo -e "${YELLOW}⚠ .env file not found${NC}"
    fi
    
    echo ""
    echo "Current shell environment:"
    echo "ENVIRONMENT: ${ENVIRONMENT:-'not set'}"
    echo "DEBUG: ${DEBUG:-'not set'}"
    
    echo ""
    echo -e "${BLUE}Testing Django settings...${NC}"
    python manage.py check --deploy
}

# Main script logic
case "$1" in
    "development"|"dev")
        set_development
        ;;
    "production"|"prod")
        set_production
        ;;
    "check")
        check_environment
        ;;
    *)
        show_usage
        exit 1
        ;;
esac
