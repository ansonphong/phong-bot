#!/bin/bash

# Update system
apt-get update && apt-get upgrade -y

# Install required system packages
apt-get install -y python3-pip python3-venv ffmpeg

# Create directory structure
mkdir -p /root/phong-bot/posts

# Create virtual environment
cd /root/phong-bot
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies from requirements.txt
if [ -f requirements.txt ]; then
    pip install -r requirements.txt
else
    echo "Error: requirements.txt file not found. Please make sure it exists in /root/phong-bot."
    exit 1
fi

# Set up cron job to run every Monday, Wednesday and Friday at 7am
(crontab -l 2>/dev/null; echo "0 7 * * 1,3,5 cd /root/phong-bot && source venv/bin/activate && python3 phong-bot.py") | crontab -

# Set proper permissions
chmod 600 /root/phong-bot/.env

echo "Setup completed successfully."
