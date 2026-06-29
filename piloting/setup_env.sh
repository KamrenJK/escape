#!/bin/bash

# Environment setup script for data analysis
# Supports both venv and conda

echo "========================================="
echo "Data Analysis Environment Setup"
echo "========================================="

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check Python version
check_python_version() {
    if command_exists python3; then
        version=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
        echo "✓ Python $version found"
        
        major=$(python3 -c 'import sys; print(sys.version_info[0])')
        minor=$(python3 -c 'import sys; print(sys.version_info[1])')
        
        if [ "$major" -ge 3 ] && [ "$minor" -ge 8 ]; then
            return 0
        else
            echo "⚠️  Warning: Python 3.8+ recommended (found $version)"
            return 1
        fi
    else
        echo "❌ Python3 not found"
        return 1
    fi
}

# Setup with venv
setup_venv() {
    echo ""
    echo "Setting up with Python venv..."
    echo "---------------------------------"
    
    ENV_NAME="piloting_env"
    
    # Create virtual environment
    echo "Creating virtual environment: $ENV_NAME"
    python3 -m venv $ENV_NAME
    
    # Activate environment
    echo "Activating environment..."
    source $ENV_NAME/bin/activate
    
    # Upgrade pip
    echo "Upgrading pip..."
    pip install --upgrade pip
    
    # Install requirements
    echo "Installing requirements..."
    pip install -r requirements.txt
    
    # Install kernel for Jupyter
    echo "Installing Jupyter kernel..."
    python -m ipykernel install --user --name=$ENV_NAME --display-name="Python (Piloting Analysis)"
    
    echo ""
    echo "✅ Virtual environment setup complete!"
    echo ""
    echo "To activate this environment in the future, run:"
    echo "  source piloting_env/bin/activate"
    echo ""
    echo "To deactivate, run:"
    echo "  deactivate"
}

# Setup with conda
setup_conda() {
    echo ""
    echo "Setting up with Conda..."
    echo "---------------------------------"
    
    ENV_NAME="piloting_env"
    
    # Create conda environment
    echo "Creating conda environment: $ENV_NAME"
    conda create -n $ENV_NAME python=3.10 -y
    
    # Activate environment
    echo "Activating environment..."
    eval "$(conda shell.bash hook)"
    conda activate $ENV_NAME
    
    # Install requirements
    echo "Installing requirements..."
    pip install -r requirements.txt
    
    # Install kernel for Jupyter
    echo "Installing Jupyter kernel..."
    python -m ipykernel install --user --name=$ENV_NAME --display-name="Python (Piloting Analysis)"
    
    echo ""
    echo "✅ Conda environment setup complete!"
    echo ""
    echo "To activate this environment in the future, run:"
    echo "  conda activate piloting_env"
    echo ""
    echo "To deactivate, run:"
    echo "  conda deactivate"
}

# Main setup logic
main() {
    # Check Python
    if ! check_python_version; then
        echo ""
        echo "Please install Python 3.8 or later"
        exit 1
    fi
    
    # Check for package managers
    echo ""
    echo "Select environment manager:"
    echo "1) venv (Python built-in)"
    echo "2) conda (Anaconda/Miniconda)"
    echo "3) Exit"
    echo ""
    read -p "Enter choice [1-3]: " choice
    
    case $choice in
        1)
            setup_venv
            ;;
        2)
            if command_exists conda; then
                setup_conda
            else
                echo "❌ Conda not found. Please install Anaconda or Miniconda."
                echo "   Visit: https://docs.conda.io/en/latest/miniconda.html"
                exit 1
            fi
            ;;
        3)
            echo "Exiting..."
            exit 0
            ;;
        *)
            echo "Invalid choice. Exiting..."
            exit 1
            ;;
    esac
    
    echo ""
    echo "========================================="
    echo "Setup Complete!"
    echo "========================================="
    echo ""
    echo "Next steps:"
    echo "1. Activate the environment (see instructions above)"
    echo "2. Start Jupyter: jupyter notebook"
    echo "3. Open data_analysis.ipynb"
    echo "4. Select kernel: 'Python (Piloting Analysis)'"
    echo ""
}

# Run main function
main