
#!/bin/bash

# Script to create a Python 3.11 virtual environment using uv with pip
# Author: Assistant
# Date: 2026-03-02

set -e  # Exit on any error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
COLOR='\033[2;33m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_success() {
    echo -e "${GREEN}[$1] √ ${NC} $2"
}

print_doing() {
    echo -en "${COLOR}[$1]${NC} $2 ${COLOR} ... ${NC}"
}

print_status() {
    echo -e "${NC}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1 ${YELLOW}!${NC}"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1 ${RED}×${NC}"
}

# Function to check if command exists
command_exists() {
    command -v "$1" &> /dev/null
}


check_uv(){
    print_doing "CHINKING" "UV"
    if ! command_exists uv; then
        print_error "uv is not installed"
        print_doing "INSTING" "uv"
        curl -LsSf https://astral.sh/uv/install.sh | sh
    else
        print_success "DONE"
    fi
}

check_env_path(){
    print_doing "CHINKING" "ENV"
    if [ ! -d ".env" ]; then
        print_warning ".env not found"
        create_env
    fi
}


create_env(){
    print_doing "creating env"
    uv venv ".env" --python 3.11
    # uv pip install --upgrade pip

    # Activate environment
    if [ -f ".env/bin/activate" ]; then
        source ".env/bin/activate"
        print_status "Environment activated"
    else
        print_error "Failed to activate environment. Activation script not found."
        create_env
    fi
    print_success "Done"
}

activate_env(){
    source .env/bin/activate
    print_status "Installing/upgrading pip..."
    print_status "Environment setup completed successfully!"
    print_status "Environment details:"
    echo "  Python: $(python --version)"
    echo "  Pip: $(pip --version)"
    echo "  Location: $(pwd)/.env"  
}

check_python_version(){
    print_doing "checking python version"
    if [ -f ".env/bin/python" ]; then
        local python_version=$( ".env/bin/python" --version 2>&1 )
        if [[ "$python_version" == *"3.11"* ]]; then
            print_success "DONE" "python version is 3.11"
            else
            print_warning "Python version in environment: $python_version"
        fi
    else
        print_warning "Not Found Python"
        create_env
    fi

    # if [ -f ".env/bin/pip" ]; then
    #     # local python_version=$( ".env/bin/python" --version 2>&1 )
    #     # if [[ "$python_version" == *"3.11"* ]]; then
    #     #     print_success "DONE" "python version is 3.11"
    #     #     else
    #     #     print_warning "Python version in environment: $python_version"
    #     # fi
    #     echo
    # else
    #     print_warning "Not Found pip"
    #     uv pip install --upgrade pip
    # fi
}

install_requirements(){
    print_doing "install_requirements"
    export UV_LINK_MODE=copy
    uv pip install -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt
    print_success "DONE" "ok"
}

main() {
    check_uv
    check_env_path
    check_python_version
    activate_env
    install_requirements
}

# Run main function with all arguments
main "$@"
