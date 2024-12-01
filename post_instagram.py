import logging
import json
import time
import os
from typing import Optional, List
from instagrapi import Client
from instagrapi.types import Media
from post_base import BasePoster, PostContent
from pathlib import Path

class InstagramPoster(BasePoster):
    def __init__(self, config: dict):
        """Initialize Instagram poster with configuration."""
        super().__init__(config)
        self.logger = logging.getLogger(__name__)
        self.instagram_enabled = config.get('instagram', {}).get('enabled', False)
        
        # Get content limits from config or use defaults
        content_config = config.get('content', {})
        self.max_images = content_config.get('max_images', 10)  # Instagram carousel limit
        self.max_image_size_mb = content_config.get('max_image_size_mb', 8)  # Instagram image limit
        self.max_video_size_mb = content_config.get('max_video_size_mb', 100)  # Instagram video limit

        # Platform-specific limits
        instagram_config = config.get('instagram', {})
        self.instagram_text_limit = instagram_config.get('text_limit', 2200)  # Instagram caption limit
        
        if not self.instagram_enabled:
            raise ValueError("Instagram posting is not enabled in config")
            
        self._init_client(config)

    def _init_client(self, config: dict):
        """Initialize client using Instagram credentials."""
        try:
            creds = config.get('instagram', {})
            required_keys = ['username', 'password']
            missing_keys = [key for key in required_keys if not creds.get(key)]
            if missing_keys:
                raise ValueError(f"Missing required Instagram configuration keys: {missing_keys}")
            
            self.client = Client()
            
            # Try to load existing session
            session_file = Path("instagram_session.json")
            if session_file.exists():
                try:
                    self.client.load_settings(str(session_file))
                    self.client.get_timeline_feed()  # Test the session
                    self.user_id = self.client.user_id
                    self.logger.info("Loaded existing Instagram session")
                    return
                except Exception as e:
                    self.logger.warning(f"Failed to load existing session: {e}")
                    session_file.unlink(missing_ok=True)
            
            # Login with username and password
            self.logger.info("Logging in to Instagram...")
            self.client.login(creds['username'], creds['password'])
            self.user_id = self.client.user_id
            
            # Save session for future use
            self.client.dump_settings(str(session_file))
            self.logger.info("Instagram Authentication Successful")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize client: {str(e)}")
            raise

    def _validate_media_file(self, filepath: str) -> bool:
        """Validate media file before upload."""
        try:
            if not os.path.isfile(filepath):
                self.logger.error(f"File {filepath} does not exist")
                return False
                
            if not os.access(filepath, os.R_OK):
                self.logger.error(f"File {filepath} is not readable")
                return False

            file_size = os.path.getsize(filepath)
            
            # Check if it's a video
            if filepath.lower().endswith(('.mp4', '.mov')):
                max_size = self.max_video_size_mb * 1024 * 1024
                if file_size > max_size:
                    self.logger.error(f"Video file {filepath} exceeds {self.max_video_size_mb}MB limit")
                    return False
            else:
                max_size = self.max_image_size_mb * 1024 * 1024
                if file_size > max_size:
                    self.logger.error(f"Image file {filepath} exceeds {self.max_image_size_mb}MB limit")
                    return False
                
            self.logger.info(f"File {filepath} validated successfully ({file_size/1024/1024:.2f}MB)")
            return True
            
        except Exception as e:
            self.logger.error(f"Error validating file {filepath}: {str(e)}")
            return False

    def validate_post_content(self, post: PostContent) -> bool:
        """Validate post content with Instagram limits."""
        try:
            # Basic content validation
            if not any([post.main_text, post.images, post.video]):
                self.logger.error("Post has no content (no text, images, or video)")
                return False

            # Text validation
            if post.main_text:
                text_length = len(post.main_text)
                if text_length > self.instagram_text_limit:
                    self.logger.error(f"Instagram caption too long ({text_length} chars, max {self.instagram_text_limit})")
                    return False

            # Alt text validation
            if post.alt_text and len(post.alt_text) > 1000:  # Standard limit
                self.logger.error(f"Alt text too long ({len(post.alt_text)} chars, max 1000)")
                return False

            # Media validation
            if post.images:
                if len(post.images) > self.max_images:
                    self.logger.error(f"Too many images ({len(post.images)}, max {self.max_images})")
                    return False
                
                for image in post.images:
                    if not self._validate_media_file(image):
                        return False

            if post.video:
                if post.images:
                    self.logger.error("Cannot post both video and images")
                    return False
                if not self._validate_media_file(post.video):
                    return False

            return True
            
        except Exception as e:
            self.logger.error(f"Error validating post content: {str(e)}")
            return False

    def post_content(self, post: PostContent) -> bool:
        """Post content to Instagram."""
        if not self.validate_post_content(post):
            return False

        try:
            # Handle media posts
            if post.images:
                if len(post.images) == 1:
                    media = self.client.photo_upload(
                        post.images[0],
                        caption=post.main_text or "",
                        extra_data={"custom_accessibility_caption": post.alt_text or ""}
                    )
                else:
                    media = self.client.album_upload(
                        post.images,
                        caption=post.main_text or "",
                        extra_data={"custom_accessibility_caption": post.alt_text or ""}
                    )
            elif post.video:
                media = self.client.video_upload(
                    post.video,
                    caption=post.main_text or "",
                    extra_data={"custom_accessibility_caption": post.alt_text or ""}
                )
            else:
                self.logger.error("Instagram requires either image or video content")
                return False

            if media:
                self.logger.info(f"Successfully posted to Instagram. Media ID: {media.pk}")
                return True
            else:
                self.logger.error("Failed to post to Instagram")
                return False

        except Exception as e:
            self.logger.error(f"Error in post_content: {str(e)}")
            return False

    def __del__(self):
        """Cleanup when object is destroyed."""
        try:
            if hasattr(self, 'client'):
                self.client.logout()
        except:
            pass