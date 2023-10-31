#!/bin/bash

# Function to check if a command exists
command_exists() {
    type "$1" &> /dev/null
}

# Check if pyenv is installed
if ! command_exists pyenv; then
    echo "Installing pyenv..."
    # Install pyenv prerequisites (Ubuntu/Debian)
    sudo apt-get update
    sudo apt-get install -y make build-essential libssl-dev zlib1g-dev \
        libbz2-dev libreadline-dev libsqlite3-dev wget curl llvm \
        libncursesw5-dev xz-utils tk-dev libxml2-dev libxmlsec1-dev libffi-dev liblzma-dev

    # Install pyenv
    git clone https://github.com/pyenv/pyenv.git ~/.pyenv
    echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ~/.bashrc
    echo 'export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.bashrc
    echo -e 'if command -v pyenv 1>/dev/null 2>&1; then\n  eval "$(pyenv init -)"\nfi' >> ~/.bashrc

    # Apply changes to current session
    export PYENV_ROOT="$HOME/.pyenv"
    export PATH="$PYENV_ROOT/bin:$PATH"
    eval "$(pyenv init -)"
fi

# Navigate to the project directory
DIR="$(dirname "$0")"
cd "$DIR" || { echo "Failed to enter directory $DIR"; exit 1; }

# Ensure .python-version exists
if [[ ! -r .python-version ]]; then
    echo ".python-version file not found or not readable"
    exit 1
fi

# Read required Python version
PYTHON_VERSION=$(cat .python-version)

# Install Python version if it's not available
if ! pyenv versions | grep -q "$PYTHON_VERSION"; then
    pyenv install "$PYTHON_VERSION" || { echo "Failed to install Python $PYTHON_VERSION"; exit 1; }
fi

# Set local Python version
pyenv local "$PYTHON_VERSION"

# Create a virtual environment using the specified Python version
"${PYENV_ROOT}/versions/${PYTHON_VERSION}/bin/python" -m venv venv || { echo "Failed to create virtual environment"; exit 1; }

echo "Setup completed. Virtual environment created in 'venv/'."
echo "Run 'source venv/bin/activate' to activate the virtual environment."
echo "Note: You might need to restart your terminal or source your profile script for 'pyenv' changes to take effect."
echo "After activating the virtual environment, install dependencies with 'pip install -r requirements.txt'."
