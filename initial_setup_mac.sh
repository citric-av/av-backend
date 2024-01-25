#!/bin/bash

# Function to check if a command exists
command_exists() {
    type "$1" &> /dev/null
}

# Check if Homebrew, pyenv, ffmpeg, and Redis are installed
if ! command_exists brew; then
    echo "Installing Homebrew..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
fi

if ! command_exists pyenv; then
    echo "Installing pyenv using Homebrew..."
    brew install pyenv
    # Initialize pyenv in the shell
    echo 'eval "$(pyenv init --path)"' >> ~/.zprofile
    echo 'eval "$(pyenv init -)"' >> ~/.zshrc
fi

if ! command_exists ffmpeg; then
    echo "Installing ffmpeg using Homebrew..."
    brew install ffmpeg
fi

if ! command_exists redis-server; then
    echo "Installing Redis server using Homebrew..."
    brew install redis
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
pyenv exec python -m venv venv || { echo "Failed to create virtual environment"; exit 1; }

# Activate the virtual environment
source venv/bin/activate

# Install Python dependencies if virtual environment is active
pip install -r requirements.txt

# Display installation messages
echo -e "\nSetup completed. Virtual environment ready in 'venv/'."
echo "ffmpeg and Redis server have been installed."
echo "Note: You might need to restart your terminal or source your .zprofile/.zshrc for 'pyenv' and other changes to take effect."
