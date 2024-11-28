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

# Install Python dependencies
pip install tweepy python-dotenv pillow

# Set up cron job to run every hour
#(crontab -l 2>/dev/null; echo "0 * * * * cd /root/phong-bot && source venv/bin/activate && python3 phong-bot.py") | crontab -
# Set up cron job to run every Monday, Wednesday and Friday at 7am
(crontab -l 2>/dev/null; echo "0 7 * * 1,3,5 cd /root/phong-bot && source venv/bin/activate && python3 phong-bot.py") | crontab -


# Set proper permissions
chmod 600 /root/phong-bot/.env