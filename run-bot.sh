#!/bin/bash

# Change to the correct directory
cd /root/phong-bot

# Activate virtual environment
source venv/bin/activate

# Run the bot
python3 phong-bot.py

# Deactivate virtual environment
deactivate
