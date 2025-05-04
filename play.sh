#!/bin/bash

# Script to play games from the vibe-coding-games repo

# Check if directory argument is provided
if [ -z "$1" ]; then
  echo "Usage: $0 <game_directory>"
  echo "Example: $0 tetris"
  exit 1
fi

GAME_DIR="$1"

# Check if the directory exists
if [ ! -d "$GAME_DIR" ]; then
  echo "Error: Directory '$GAME_DIR' not found."
  exit 1
fi

# Change into the game directory
cd "$GAME_DIR" || exit 1

echo "Entered directory: $(pwd)"

# Determine main script
# Assuming all projects now use uv and have a recognizable main script
MAIN_SCRIPT=""
if [ -f "main.py" ]; then
    MAIN_SCRIPT="main.py"
elif [ -f "flappy_bird.py" ]; then # Keep check for flappybird's specific name
    MAIN_SCRIPT="flappy_bird.py"
else
    echo "Error: Could not determine main script (main.py or flappy_bird.py) in '$GAME_DIR'."
    exit 1
fi

echo "Main script: $MAIN_SCRIPT"

# Setup and run using uv
echo "Using uv..."
if ! command -v uv &> /dev/null; then
    echo "Error: uv command not found. Please install uv."
    exit 1
fi

VENV_CREATED=false
# Ensure venv exists
if [ ! -d ".venv" ]; then
    echo "Virtual environment (.venv) not found. Creating..."
    uv venv || { echo "uv venv creation failed."; exit 1; }
    VENV_CREATED=true
else
    echo "Virtual environment (.venv) already exists."
fi

# Activate the environment
echo "Activating venv..."
source .venv/bin/activate || { echo "Failed to activate venv."; exit 1; }

# Install/Sync dependencies ONLY if venv was just created
if [ "$VENV_CREATED" = true ]; then
     echo "Installing/syncing dependencies into newly created venv..."
     # uv sync will automatically use pyproject.toml or uv.lock
     uv sync || { echo "uv sync failed."; deactivate; exit 1; }
fi

# Run the script
echo "Running $MAIN_SCRIPT..."
python "$MAIN_SCRIPT"

# Deactivate after script finishes
echo "Deactivating venv..."
deactivate

echo "Game exited."
exit 0
