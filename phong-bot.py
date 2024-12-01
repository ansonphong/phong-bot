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
from post_instagram import InstagramPoster  # Updated import
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
        if self.config['instagram']['enabled']:  # Removed threads condition
            self.posters.append(InstagramPoster(self.config))  # Updated class name
        
        if not self.posters:
            self.logger.warning("No social media platforms are enabled in config")
        
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
        # Get all files that don't start with .
        all_files = {f.name for f in self.posts_dir.iterdir() if f.is_file() and not f.name.startswith('.')}
        
        # Get unique basenames, removing both numeric suffixes and alt suffixes
        unique_basenames = {self._get_basename_without_number(f) for f in all_files}
        posted_basenames = self._get_posted_basenames()
        
        self.logger.info(f"Found files: {all_files}")
        self.logger.info(f"Unique basenames: {unique_basenames}")
        self.logger.info(f"Posted basenames: {posted_basenames}")
        
        return list(unique_basenames - posted_basenames)

    def _get_basename_without_number(self, filename: str) -> str:
        """Extract basename without number suffix and alt suffix."""
        base = Path(filename).stem
        
        # First remove the -alt suffix if present
        if base.endswith('-alt'):
            base = base[:-4]  # Remove '-alt'
            
        # Then handle numeric suffix
        if '-' in base:
            parts = base.rsplit('-', 1)
            if parts[1].isdigit():
                return parts[0]
                
        return base

    def _build_post_content(self, basename: str) -> PostContent:
        """Build post content object from files matching basename."""
        post = PostContent(basename=basename)
        self.logger.info(f"Building post content for basename: {basename}")
        
        # List all matching files before processing
        files = list(self.posts_dir.glob(f"{basename}*"))
        self.logger.info(f"Found {len(files)} files matching basename: {[f.name for f in files]}")
        
        for file in files:
            suffix = file.suffix.lower()
            stem = file.stem
            
            # Log each file being processed
            self.logger.info(f"Processing file: {file} (suffix: {suffix}, stem: {stem})")
            
            if suffix == '.txt':
                with open(file, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    if stem.endswith('-alt'):
                        post.alt_text = content
                        self.logger.info(f"Added alt text: {len(content)} chars")
                    else:
                        post.main_text = content
                        self.logger.info(f"Added main text: {len(content)} chars")
            elif suffix in {'.jpg', '.jpeg', '.png', '.gif'}:
                post.images.append(str(file))
                self.logger.info(f"Added image: {file}")
            elif suffix in {'.mp4', '.mov'}:
                post.video = str(file)
                self.logger.info(f"Added video: {file}")
        
        if post.images:
            post.images.sort()
            self.logger.info(f"Final image list: {post.images}")
            
        # Log final post content summary
        self.logger.info(f"Post content summary:")
        self.logger.info(f"- Has main text: {bool(post.main_text)}")
        self.logger.info(f"- Has alt text: {bool(post.alt_text)}")
        self.logger.info(f"- Number of images: {len(post.images)}")
        self.logger.info(f"- Has video: {bool(post.video)}")
        
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
                
            if not self.posters:
                self.logger.error("No social media platforms are enabled")
                return False
            
            selected_basename = random.choice(available_posts)
            post_content = self._build_post_content(selected_basename)
            
            success = True
            for poster in self.posters:
                if not poster.post_content(post_content):
                    self.logger.error(f"Failed to post using {poster.__class__.__name__}")
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