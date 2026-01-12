#!/bin/bash

# Exit if any command fails
#set -e
#deactivate

# Create virtual environment
python -m venv .card_game_venv

# Activate the virtual environment
source .card_game_venv/bin/activate

# Upgrade pip and install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Add Jupyter kernel
# python -m ipykernel install --user --name=.card_game_venv --display-name "Python (.card_game_venv)"

#nbstripout --install

# installs as package
pip install -e .


# To run, use - source setup.sh - in the command terminal