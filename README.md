
# 🐸🤖 PHONG-BOT
### For automatic random auto-posting to social media.

A robust Python-based X/Twitter bot that automatically posts content from a local directory to X.com. The bot intelligently handles multiple images, videos, text content, and alt text while tracking what has been posted to prevent duplicates.

## Features

- 🎯 Smart content management with basename tracking
- 🖼️ Support for multiple images in a single post
- 🎥 Video posting capabilities
- ♿ Alt text support for accessibility
- 📝 Text content management
- 🔄 Random post selection
- 📊 Detailed logging
- ✅ Posted content tracking
- 🔒 Secure credential management

## Table of Contents

- [Requirements](#requirements)
- [Installation](#installation)
- [Configuration](#configuration)
- [File Structure](#file-structure)
- [Usage](#usage)
- [Content Management](#content-management)
- [Automated Posting](#automated-posting)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [License](#license)

## Requirements

- Python 3.7+
- Twitter Developer Account with Elevated Access
- Required Python packages:
  ```
  tweepy>=4.10.0
  python-dotenv>=0.19.0
  ```

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/twitter-auto-poster.git
   cd twitter-auto-poster
   ```

2. Install required packages:
   ```bash
   pip install -r requirements.txt
   ```

3. Create a `.env` file in the root directory:
   ```env
   TWITTER_API_KEY=your_api_key
   TWITTER_API_SECRET=your_api_secret
   TWITTER_ACCESS_TOKEN=your_access_token
   TWITTER_ACCESS_TOKEN_SECRET=your_access_token_secret
   TWITTER_BEARER_TOKEN=your_bearer_token
   ```

## Configuration

### Twitter Developer Account Setup

1. Go to [Twitter Developer Portal](https://developer.twitter.com/en/portal/dashboard)
2. Create a new project and app
3. Enable OAuth 1.0a and OAuth 2.0
4. Set app permissions to "Read and Write"
5. Generate Access Token and Secret
6. Enable Elevated access for media upload capabilities

## File Structure

```
phong-bot/
├── posts/                  # Content directory
│   ├── posted.txt         # Tracks posted content
│   ├── example-1.jpg      
│   ├── example-2.jpg
│   ├── example.txt
│   └── example-alt.txt
├── .env                   # Environment variables
├── requirements.txt       # Python dependencies
├── phong-bot.py           # Main script
└── README.md              # Documentation
```

## Content Management

### Supported File Formats

- Images: `.jpg`, `.jpeg`, `.png`, `.gif`
- Videos: `.mp4`, `.mov`
- Text: `.txt`

### File Naming Conventions

The bot supports various content combinations through specific naming conventions:

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

4. Text Only:
   ```
   mypost.txt
   ```

5. Image Only:
   ```
   mypost.jpg
   ```

6. Image with Alt Text Only:
   ```
   mypost.jpg
   mypost-alt.txt
   ```

7. Video with Text:
   ```
   mypost.mp4
   mypost.txt
   ```

### Content Guidelines

- Images must be under 5MB
- Videos must be under 512MB
- Alt text should be descriptive and under 1000 characters
- Tweet text should be under 280 characters

## Usage

### Basic Usage

Run the script manually:
```bash
python phong-bot.py
```

### Automated Posting

#### Using Cron (Linux/Mac)

1. Open your crontab:
   ```bash
   crontab -e
   ```

2. Add a schedule (e.g., every 6 hours):
   ```bash
   0 */6 * * * cd /path/to/twitter-auto-poster && /usr/bin/python3 phong-bot.py
   ```

#### Using Task Scheduler (Windows)

1. Open Task Scheduler
2. Create Basic Task
3. Set trigger (e.g., daily)
4. Action: Start a program
   - Program/script: `python`
   - Arguments: `phong-bot.py`
   - Start in: `C:\path\to\phong-bot`

### Logging

The bot creates a detailed log file `x_poster.log` containing:
- Authentication status
- Media upload progress
- Errors and exceptions
- Successful posts

## How It Works

1. **Content Discovery**
   - Scans `/posts` directory
   - Creates list of unique basenames
   - Filters out already posted content

2. **Content Selection**
   - Randomly selects from available content
   - Groups related files by basename

3. **Content Processing**
   - Consolidates media files
   - Reads text content
   - Processes alt text

4. **Posting**
   - Uploads media
   - Creates tweet
   - Updates `posted.txt`

## Troubleshooting

### Common Issues

1. **403 Forbidden Error**
   - Check API access level
   - Verify token permissions
   - Regenerate access tokens

2. **Media Upload Fails**
   - Verify file size limits
   - Check file format
   - Ensure proper permissions

3. **Authentication Failed**
   - Verify .env file configuration
   - Check token validity
   - Ensure elevated access

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.
Copyright (C) 2024 Anson Phong
