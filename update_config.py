import json
import os
from pathlib import Path

def update_env_file():
    """Update .env file from config.json"""
    try:
        # Read config.json
        with open('config.json', 'r') as f:
            config = json.load(f)
        
        # Create .env content
        env_content = []
        
        # Add X/Twitter credentials
        if config['x']['enabled']:
            env_content.extend([
                f"TWITTER_API_KEY={config['x']['api_key']}",
                f"TWITTER_API_SECRET={config['x']['api_secret']}",
                f"TWITTER_ACCESS_TOKEN={config['x']['access_token']}",
                f"TWITTER_ACCESS_TOKEN_SECRET={config['x']['access_token_secret']}",
                f"TWITTER_BEARER_TOKEN={config['x']['bearer_token']}"
            ])
        
        # Add Threads credentials
        if config['threads']['enabled']:
            env_content.extend([
                f"THREADS_API_KEY={config['threads']['api_key']}",
                f"THREADS_API_SECRET={config['threads']['api_secret']}",
                f"THREADS_ACCESS_TOKEN={config['threads']['access_token']}",
                f"THREADS_USERNAME={config['threads']['instagram_username']}",
                f"THREADS_PASSWORD={config['threads']['instagram_password']}"
            ])
        
        # Write to .env file
        with open('.env', 'w') as f:
            f.write('\n'.join(env_content))
        
        # Set proper permissions on Unix-like systems
        if os.name != 'nt':
            Path('.env').chmod(0o600)
            
        print("Successfully updated .env file")
        
    except Exception as e:
        print(f"Error updating .env file: {str(e)}")

if __name__ == "__main__":
    update_env_file()




