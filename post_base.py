import os
import logging
from pathlib import Path
from typing import List, Optional
from dataclasses import dataclass
from abc import ABC, abstractmethod

@dataclass
class PostContent:
    basename: str
    main_text: Optional[str] = None
    alt_text: Optional[str] = None
    images: List[str] = None
    video: Optional[str] = None

    def __post_init__(self):
        if self.images is None:
            self.images = []

class BasePoster(ABC):
    def __init__(self, config: dict):
        """Initialize base poster with configuration."""
        self.config = config
        
        # Setup logging
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Add platform-specific file handler
        fh = logging.FileHandler(f"{self.__class__.__name__.lower()}.log")
        fh.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        self.logger.addHandler(fh)

    @abstractmethod
    def post_content(self, post: PostContent) -> bool:
        """Post content to platform. Must be implemented by subclasses."""
        pass

    def _validate_media_file(self, filepath: str) -> bool:
        """Validate media file before upload."""
        try:
            file_size = os.path.getsize(filepath)
            
            # Check if it's a video
            if filepath.lower().endswith(('.mp4', '.mov')):
                max_size = self.config['content']['max_video_size_mb'] * 1024 * 1024
                if file_size > max_size:
                    self.logger.error(f"Video file {filepath} exceeds {self.config['content']['max_video_size_mb']}MB limit")
                    return False
            else:
                max_size = self.config['content']['max_image_size_mb'] * 1024 * 1024
                if file_size > max_size:
                    self.logger.error(f"Image file {filepath} exceeds {self.config['content']['max_image_size_mb']}MB limit")
                    return False
            
            # Check file existence and accessibility
            if not os.path.isfile(filepath):
                self.logger.error(f"File {filepath} does not exist")
                return False
                
            if not os.access(filepath, os.R_OK):
                self.logger.error(f"File {filepath} is not readable")
                return False
                
            self.logger.info(f"File {filepath} validated successfully ({file_size/1024/1024:.2f}MB)")
            return True
            
        except Exception as e:
            self.logger.error(f"Error validating file {filepath}: {str(e)}")
            return False

    def validate_post_content(self, post: PostContent) -> bool:
        """Validate post content before posting."""
        try:
            # Validate text content
            if post.main_text:
                # Get platform-specific character limit
                char_limit = self.config[self.__class__.__name__.lower().replace('poster', '')].get('text_limit', 280)
                if len(post.main_text) > char_limit:
                    self.logger.error(f"Main text exceeds {char_limit} characters: {len(post.main_text)}")
                    return False
                
            if post.alt_text and len(post.alt_text) > 1000:  # Common alt text limit
                self.logger.error(f"Alt text exceeds 1000 characters: {len(post.alt_text)}")
                return False

            # Validate images
            if post.images:
                if len(post.images) > self.config['content']['max_images']:
                    self.logger.error(f"Too many images: {len(post.images)} (max: {self.config['content']['max_images']})")
                    return False
                    
                for image in post.images:
                    if not self._validate_media_file(image):
                        return False

            # Validate video
            if post.video:
                if post.images:
                    self.logger.error("Cannot post both video and images")
                    return False
                if not self._validate_media_file(post.video):
                    return False

            # Validate that there's some content to post
            if not any([post.main_text, post.images, post.video]):
                self.logger.error("Post has no content (no text, images, or video)")
                return False

            return True
            
        except Exception as e:
            self.logger.error(f"Error validating post content: {str(e)}")
            return False