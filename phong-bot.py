#    @..@ 
#   (----)
#  ( >__< )
#  ^^ ~~ ^^      
# PHONG-BOT                                     
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY. See the GNU General Public License for more details.
# See <https://www.gnu.org/licenses/gpl-3.0.txt>
# Created with Claude AI
# Copyright (C) 2024 Anson Phong : https://phong.com

import json
import random
import logging
from pathlib import Path
from typing import List, Set

from post_x import XPoster
from post_threads import ThreadsPoster
from post_base import PostContent

class PhongBot:
    def __init__(self, config_file: str = "config.json"):
        """Initialize the social media bot."""
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('phong_bot.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
        # Load configuration
        with open(config_file, 'r') as f:
            self.config = json.load(f)
        
        # Initialize posters
        self.posters = []
        if self.config['x']['enabled']:
            self.posters.append(XPoster(self.config))
        if self.config['threads']['enabled']:
            self.posters.append(ThreadsPoster(self.config))
        
        # Initialize paths
        self.posts_dir = Path(self.config['content']['posts_directory'])
        self.posted_file = self.posts_dir / "posted.txt"
        self.posts_dir.mkdir(exist_ok=True)

    def _get_posted_basenames(self) -> Set[str]:
        """Read and return set of already posted basenames."""
        if not self.posted_file.exists():
            return set()
        
        with open(self.posted_file, 'r') as f:
            return {line.strip() for line in f if line.strip()}

    def _get_available_posts(self) -> List[str]:
        """Get list of available posts that haven't been posted."""
        all_files = {f.name for f in self.posts_dir.iterdir() if f.is_file()}
        posted_basenames = self._get_posted_basenames()
        
        unique_basenames = {
            self._get_basename_without_number(f)
            for f in all_files
            if not f.startswith('.') and f != 'posted.txt'
        }
        
        return list(unique_basenames - posted_basenames)

    def _get_basename_without_number(self, filename: str) -> str:
        """Extract basename without number suffix and extension."""
        base = Path(filename).stem
        if '-' in base:
            parts = base.rsplit('-', 1)
            if parts[1].isdigit():
                return parts[0]
        return base

    def _build_post_content(self, basename: str) -> PostContent:
        """Build post content object from files matching basename."""
        post = PostContent(basename=basename)
        files = list(self.posts_dir.glob(f"{basename}*"))
        
        for file in files:
            suffix = file.suffix.lower()
            stem = file.stem
            
            if suffix == '.txt':
                with open(file, 'r', encoding='utf-8') as f:
                    if stem.endswith('-alt'):
                        post.alt_text = f.read().strip()
                    else:
                        post.main_text = f.read().strip()
            elif suffix in {'.jpg', '.jpeg', '.png', '.gif'}:
                post.images.append(str(file))
            elif suffix in {'.mp4', '.mov'}:
                post.video = str(file)
        
        post.images.sort()
        return post

    def _mark_as_posted(self, basename: str):
        """Mark basename as posted."""
        with open(self.posted_file, 'a') as f:
            f.write(f"{basename}\n")

    def post_random_content(self) -> bool:
        """Post random content to all enabled platforms."""
        try:
            available_posts = self._get_available_posts()
            
            if not available_posts:
                self.logger.info("No new content available to post")
                return False
            
            selected_basename = random.choice(available_posts)
            post_content = self._build_post_content(selected_basename)
            
            success = True
            for poster in self.posters:
                if not poster.post_content(post_content):
                    success = False
            
            if success:
                self._mark_as_posted(selected_basename)
                self.logger.info(f"Successfully posted content: {selected_basename}")
                
            return success
            
        except Exception as e:
            self.logger.error(f"Error in post_random_content: {e}")
            return False

if __name__ == "__main__":
    import argparse
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Phong Bot - Social Media Auto Poster')
    parser.add_argument('--config', default='config.json', help='Path to config file')
    args = parser.parse_args()
    
    # Create and run bot
    try:
        bot = PhongBot(config_file=args.config)
        success = bot.post_random_content()
        exit(0 if success else 1)
    except Exception as e:
        logging.error(f"Bot failed to run: {str(e)}")
        exit(1)