import logging
import json
import time
import os
from typing import Optional, List, Tuple
from instagrapi import Client
from instagrapi.types import Media, Location, Usertag
from post_base import BasePoster, PostContent
from pathlib import Path
from PIL import Image

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
        
        # Maximum dimension for Instagram images (4K)
        self.max_dimension = 3840

        # Platform-specific limits
        instagram_config = config.get('instagram', {})
        self.instagram_text_limit = instagram_config.get('text_limit', 2200)  # Instagram caption limit
        
        # Setup JPG directory
        self.posts_dir = Path(config['content']['posts_directory'])
        self.jpg_dir = self.posts_dir / "JPG"
        self.jpg_dir.mkdir(exist_ok=True)
        
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
            self.client.delay_range = [1, 3]  # Add some delay between requests
            
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
        """Validate post content before uploading."""
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

    def _process_image(self, image_path: str) -> Tuple[str, bool]:
        """Process image for Instagram upload.
        Returns tuple of (processed_image_path, is_temporary)
        """
        try:
            # Open the image
            with Image.open(image_path) as img:
                needs_processing = False
                
                # Check if image needs to be resized
                max_size = max(img.size)
                if max_size > self.max_dimension:
                    needs_processing = True
                    ratio = self.max_dimension / max_size
                    new_size = tuple(int(dim * ratio) for dim in img.size)
                    self.logger.info(f"Resizing image from {img.size} to {new_size}")
                    img = img.resize(new_size, Image.Resampling.LANCZOS)

                # If it's a PNG or needs resizing, convert/save as JPEG
                is_png = image_path.lower().endswith('.png')
                if is_png or needs_processing:
                    # Create a filename based on original filename
                    orig_name = Path(image_path).stem
                    jpg_path = self.jpg_dir / f"{orig_name}.jpg"
                    
                    # Convert to RGB if necessary (for PNG with transparency)
                    if img.mode in ('RGBA', 'LA') or (img.mode == 'P' and 'transparency' in img.info):
                        self.logger.info("Converting transparent PNG to RGB")
                        background = Image.new('RGB', img.size, (255, 255, 255))
                        if img.mode == 'P':
                            img = img.convert('RGBA')
                        background.paste(img, mask=img.split()[3] if img.mode == 'RGBA' else None)
                        img = background

                    # Save as JPEG with high quality
                    self.logger.info(f"Saving image as JPEG: {jpg_path}")
                    img.save(jpg_path, 'JPEG', quality=100)
                    
                    # Verify file size
                    file_size = os.path.getsize(jpg_path) / (1024 * 1024)  # Convert to MB
                    if file_size > self.max_image_size_mb:
                        # If still too large, reduce quality until it fits
                        quality = 95
                        while file_size > self.max_image_size_mb and quality > 40:
                            quality -= 5
                            img.save(jpg_path, 'JPEG', quality=quality)
                            file_size = os.path.getsize(jpg_path) / (1024 * 1024)
                            self.logger.info(f"Reduced image quality to {quality}, new size: {file_size:.2f}MB")

                    return str(jpg_path), True
                
                return image_path, False

        except Exception as e:
            self.logger.error(f"Error processing image {image_path}: {str(e)}")
            raise

    def post_content(self, post: PostContent) -> bool:
        """Post content to Instagram."""
        if not self.validate_post_content(post):
            return False

        processed_files = []  # Track processed files for cleanup
        
        try:
            # Handle media posts
            if post.images:
                # Process images and get their paths
                processed_images = []
                for img_path in post.images:
                    processed_path, is_processed = self._process_image(img_path)
                    processed_images.append(processed_path)
                    if is_processed:
                        processed_files.append(processed_path)

                # Convert paths to absolute paths
                image_paths = [str(Path(img).absolute()) for img in processed_images]
                
                self.logger.info(f"Attempting to post {len(image_paths)} images to Instagram")
                for path in image_paths:
                    self.logger.info(f"Image path: {path}")

                try:
                    if len(post.images) == 1:
                        self.logger.info("Posting single image")
                        media = self.client.photo_upload(
                            path=image_paths[0],
                            caption=post.main_text or ""
                        )
                        self.logger.info(f"Successfully posted single image to Instagram. Media ID: {media.pk}")
                    else:
                        self.logger.info("Posting multiple images as carousel/album")
                        media = self.client.album_upload(
                            paths=image_paths,
                            caption=post.main_text or ""
                        )
                        self.logger.info(f"Successfully posted album to Instagram. Media ID: {media.pk}")
                    return True
                    
                except Exception as e:
                    self.logger.error(f"Failed to post {'album' if len(post.images) > 1 else 'single image'}: {str(e)}")
                    raise

            elif post.video:
                video_path = str(Path(post.video).absolute())
                self.logger.info(f"Attempting to post video: {video_path}")
                try:
                    media = self.client.video_upload(
                        path=video_path,
                        caption=post.main_text or ""
                    )
                    self.logger.info(f"Successfully posted video to Instagram. Media ID: {media.pk}")
                    return True
                except Exception as e:
                    self.logger.error(f"Failed to post video: {str(e)}")
                    raise
            else:
                self.logger.error("Instagram requires either image or video content")
                return False

        except Exception as e:
            self.logger.error(f"Error posting to Instagram: {str(e)}")
            
            # If session expired, try to re-login
            if "login_required" in str(e).lower():
                self.logger.info("Session expired, attempting to re-login...")
                try:
                    session_file = Path("instagram_session.json")
                    session_file.unlink(missing_ok=True)
                    self._init_client(self.config)
                    return self.post_content(post)  # Retry the post
                except Exception as re_login_error:
                    self.logger.error(f"Failed to re-login: {str(re_login_error)}")
            
            return False
            
        finally:
            # Clean up processed files
            for processed_file in processed_files:
                try:
                    os.unlink(processed_file)
                    self.logger.info(f"Cleaned up processed file: {processed_file}")
                except Exception as e:
                    self.logger.warning(f"Failed to clean up processed file {processed_file}: {str(e)}")

    def __del__(self):
        """Cleanup when object is destroyed."""
        try:
            if hasattr(self, 'client'):
                self.client.logout()
        except:
            pass