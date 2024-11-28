# 🐸🤖 PHONG-BOT
### Automated Social Media Content Posting Bot

A robust Python-based social media bot that automatically posts content from a local directory to multiple platforms. The bot intelligently handles multiple images, videos, text content, and alt text while tracking what has been posted to prevent duplicates.

## Features

- 🎯 Multi-platform support (X/Twitter and Meta Threads)
- 🖼️ Support for multiple images in a single post
- 🎥 Video posting capabilities
- ♿ Alt text support for accessibility
- 📝 Text content management
- 🔄 Random post selection
- 📊 Detailed logging
- ✅ Posted content tracking
- 🔒 Secure credential management via config.json
- 📅 Flexible scheduling options

## Requirements

- Python 3.7+
- Required Python packages (see requirements.txt):
  ```
  certifi==2024.8.30
  charset-normalizer==3.4.0
  idna==3.10
  oauthlib==3.2.2
  pillow==11.0.0
  python-dotenv==1.0.1
  requests==2.32.3
  requests-oauthlib==1.3.1
  tweepy==4.14.0
  urllib3==2.2.3
  ```

## Installation

### Windows
```batch
# Run setup script
setup.bat
```

### Linux/Mac
```bash
# Run setup script
chmod +x setup.sh
./setup.sh
```


## Configuration

1. Copy the sample configuration file:
```bash
cp config-sample.json config.json
```

2. Edit `config.json` with your credentials and settings:
```json
{
    "x": {
        "enabled": true,
        "api_key": "your_api_key",
        "api_secret": "your_api_secret",
        "access_token": "your_access_token",
        "access_token_secret": "your_access_token_secret",
        "bearer_token": "your_bearer_token",
         "text_limit": 280 // 280 for free accounts or 25000 for premium accounts
    },
    "threads": {
        "enabled": false,
        "api_key": "",
        "api_secret": "",
        "access_token": "",
        "instagram_username": "",
        "instagram_password": ""
    },
    "posting_schedule": {
        "days": [1, 3, 5],
        "hour": 7,
        "minute": 0
    },
    "content": {
        "posts_directory": "posts",
        "max_images": 4,
        "max_image_size_mb": 5,
        "max_video_size_mb": 512
    }
}
```

A sample configuration file (`config-sample.json`) is provided in the repository. This file contains the structure of the configuration with placeholder values. Simply copy this file to `config.json` and update it with your actual credentials and preferences.

Never commit your actual `config.json` file containing real credentials to version control. The `.gitignore` file is set up to exclude this file by default.



## File Structure

```
phong-bot/
├── posts/                 # Content directory
│   └── posted.txt         # Tracks posted content
├── post_base.py           # Base class for all platforms
├── post_x.py              # X/Twitter implementation
├── post_threads.py        # Threads implementation
├── phong-bot.py           # Main bot logic
├── update_config.py       # Config management
├── config.json            # Central configuration
├── requirements.txt       # Python dependencies
├── setup.bat              # Windows setup script
├── setup.sh               # Linux setup script
└── README.md              # Documentation
```

## Content Management

### Supported File Types
- Images: `.jpg`, `.jpeg`, `.png`, `.gif`
- Videos: `.mp4`, `.mov`
- Text: `.txt`

### File Naming Conventions

1. Multiple Images with Text:
```
mypost-1.jpg
mypost-2.jpg
mypost-3.jpg
mypost.txt
```

2. Single Image with Text:
```
mypost.jpg
mypost.txt
```

3. Image with Alt Text:
```
mypost.jpg
mypost-alt.txt
```

4. Video with Text:
```
mypost.mp4
mypost.txt
```

### Content Guidelines
- Images must be under 5MB
- Videos must be under 512MB
- Alt text should be under 1000 characters
- Tweet text should be under 280 characters

## Usage

### Manual Run
Windows:
```batch
run-bot.bat
```

Linux/Mac:
```bash
./run-bot.sh
```

### Automated Scheduling

#### Windows Task Scheduler
```batch
# Default schedule (M/W/F at 7am)
task-setup.bat

# Daily at 7am
task-setup.bat daily

# Weekly on Monday at 7am
task-setup.bat weekly
```

#### Linux Cron
Add to crontab:
```bash
# Run M/W/F at 7am
0 7 * * 1,3,5 /path/to/phong-bot/run-bot.sh
```

## Logging

The bot creates detailed logs in:
- `phong_bot.log` - General application logs
- `x_poster.log` - X/Twitter specific logs
- `threads_poster.log` - Threads specific logs

Logs include:
- Authentication status
- Media upload progress
- Content processing details
- Errors and exceptions
- Successful posts

## Platform Support

### X/Twitter
- Full API support via tweepy
- Media upload with alt text
- Rate limit handling
- Error recovery

### Meta Threads
- Basic implementation ready
- Awaiting public API availability
- Follows same content structure as X/Twitter

## Troubleshooting

### Common Issues

1. Authentication Errors:
   - Verify credentials in config.json
   - Run update_config.py after changes
   - Check platform API status

2. Media Upload Failures:
   - Verify file sizes
   - Check file permissions
   - Ensure proper file formats

3. Scheduling Issues:
   - Check system time/timezone
   - Verify script paths
   - Check log files for errors

## License

GPL-3.0 License - see LICENSE for details.  
Copyright (C) 2024 Anson Phong