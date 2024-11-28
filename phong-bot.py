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
# Copyright (C) 2024 Anson Phong : @ansonphong : https://phong.com

import json
import random
import logging
import shutil
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
        self.posted_dir = self.posts_dir / "posted"
        
        # Create required directories
        self.posts_dir.mkdir(exist_ok=True)
        self.posted_dir.mkdir(exist_ok=True)

    def _get_posted_basenames(self) -> Set[str]:
        """Get set of already posted basenames by checking posted directory."""
        posted_files = list(self.posted_dir.iterdir())
        return {self._get_basename_without_number(f.name) for f in posted_files if f.is_file()}

    def _get_available_posts(self) -> List[str]:
        """Get list of available posts that haven't been posted."""
        all_files = {f.name for f in self.posts_dir.iterdir() if f.is_file() and not f.name.startswith('.')}
        unique_basenames = {self._get_basename_without_number(f) for f in all_files}
        posted_basenames = self._get_posted_basenames()
        
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

    def _move_to_posted(self, basename: str):
        """Move all files with given basename to posted directory."""
        try:
            files = list(self.posts_dir.glob(f"{basename}*"))
            for file in files:
                target_path = self.posted_dir / file.name
                shutil.move(str(file), str(target_path))
                self.logger.info(f"Moved {file.name} to posted directory")
        except Exception as e:
            self.logger.error(f"Error moving files to posted directory: {e}")
            raise

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
                self._move_to_posted(selected_basename)
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