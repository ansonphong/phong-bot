import os
import logging
import tweepy
from typing import List, Optional
from post_base import BasePoster, PostContent

class XPoster(BasePoster):
    def __init__(self, config: dict):
        """Initialize X/Twitter poster with configuration."""
        super().__init__(config)
        self.logger = logging.getLogger(__name__)
        self._init_client(config['x'])
        # Override max_images specifically for X
        self.max_images = min(4, self.config['content'].get('max_images', 4))

    def _init_client(self, config: dict):
        """Initialize X/Twitter API client."""
        try:
            # Verify required credentials exist
            required_keys = ['api_key', 'api_secret', 'access_token', 
                           'access_token_secret', 'bearer_token']
            missing_keys = [key for key in required_keys if not config.get(key)]
            if missing_keys:
                raise ValueError(f"Missing required X configuration keys: {missing_keys}")

            # Initialize OAuth handler
            auth = tweepy.OAuthHandler(
                config['api_key'],
                config['api_secret']
            )
            auth.set_access_token(
                config['access_token'],
                config['access_token_secret']
            )
            
            # Initialize Tweepy client
            self.client = tweepy.Client(
                bearer_token=config['bearer_token'],
                consumer_key=config['api_key'],
                consumer_secret=config['api_secret'],
                access_token=config['access_token'],
                access_token_secret=config['access_token_secret'],
                wait_on_rate_limit=True
            )
            
            # Initialize API (needed for media upload)
            self.api = tweepy.API(auth)
            self.api.verify_credentials()
            self.logger.info("X/Twitter Authentication Successful")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize X client: {str(e)}")
            raise

    def _upload_chunked_video(self, video_path: str) -> Optional[int]:
        """Upload a video in chunks."""
        try:
            file_size = os.path.getsize(video_path)
            self.logger.info(f"[-] Initiating video upload: {os.path.basename(video_path)}")
            
            # INIT
            upload = self.api.chunked_upload(filename=video_path, file_size=file_size)
            
            # APPEND
            chunk_size = 1024 * 1024  # 1MB chunks
            with open(video_path, 'rb') as file:
                bytes_sent = 0
                while bytes_sent < file_size:
                    chunk = file.read(chunk_size)
                    if not chunk:
                        break
                    upload = self.api.chunked_upload(chunk, 
                                                file_size=file_size,
                                                media_id=upload.media_id,
                                                segment_index=bytes_sent // chunk_size)
                    bytes_sent += len(chunk)
            
            # FINALIZE
            self.logger.info("[+] Finalizing video upload...")
            media = self.api.chunked_upload(media_id=upload.media_id, status='FINALIZE')
            
            self.logger.info(f"[SUCCESS] Video upload complete - Media ID: {media.media_id}")
            return media.media_id
            
        except Exception as e:
            self.logger.error(f"[ERROR] Failed to upload video {video_path}: {str(e)}")
            return None

    def _upload_image(self, image_path: str, alt_text: Optional[str] = None) -> Optional[int]:
        """Upload an image."""
        try:
            self.logger.info(f"[-] Processing image: {os.path.basename(image_path)}")
            media = self.api.media_upload(filename=image_path)
                
            if alt_text:
                self.logger.info("[+] Adding alt text description...")
                self.api.create_media_metadata(media.media_id, alt_text)
                
            self.logger.info(f"[SUCCESS] Image uploaded successfully - Media ID: {media.media_id}")
            return media.media_id
            
        except Exception as e:
            self.logger.error(f"[ERROR] Failed to upload image {image_path}: {str(e)}")
            return None

    def post_content(self, post: PostContent) -> bool:
        """Post content to X/Twitter with elegant status messages."""
        if not self.validate_post_content(post):
            self.logger.error("[ERROR] Content validation failed")
            return False

        try:
            media_ids = []
            
            # Handle images if present
            if post.images:
                # Limit to max 4 images for X
                images_to_upload = post.images[:self.max_images]
                if len(post.images) > self.max_images:
                    self.logger.warning(f"[NOTICE] X supports maximum {self.max_images} images. Additional images will be omitted.")
                
                self.logger.info(f"\n[STARTING] Processing {len(images_to_upload)} images for upload")
                for i, image in enumerate(images_to_upload, 1):
                    if not self._validate_media_file(image):
                        self.logger.error(f"[ERROR] Image validation failed: {image}")
                        return False
                    
                    media_id = self._upload_image(image, post.alt_text)
                    if media_id:
                        media_ids.append(media_id)
                        self.logger.info(f"[PROGRESS] Image {i}/{len(images_to_upload)} processed successfully")
                    else:
                        return False

            # Handle video if present
            elif post.video:
                self.logger.info("\n[STARTING] Processing video upload")
                if not self._validate_media_file(post.video):
                    self.logger.error(f"[ERROR] Video validation failed: {post.video}")
                    return False
                
                media_id = self._upload_chunked_video(post.video)
                if media_id:
                    media_ids.append(media_id)
                else:
                    return False

            # Create the tweet
            self.logger.info("[FINALIZING] Preparing to post content...")
            response = self.client.create_tweet(
                text=post.main_text if post.main_text else None,
                media_ids=media_ids if media_ids else None
            )
            
            if response and hasattr(response, 'data'):
                tweet_id = response.data['id']
                self.logger.info(f"\n[SUCCESS] Content successfully posted to X!")
                self.logger.info(f"[DETAILS] Tweet ID: {tweet_id}")
                self.logger.info("[STATUS] All operations completed successfully")
                return True
            else:
                self.logger.error("\n[ERROR] Failed to post to X - No response data received")
                return False

        except tweepy.TweepyException as e:
            self.logger.error(f"\n[ERROR] Failed to post to X: {str(e)}")
            return False
        except Exception as e:
            self.logger.error(f"\n[ERROR] Unexpected error occurred: {str(e)}")
            return False

    def _validate_rate_limits(self):
        """Check current rate limit status."""
        try:
            limits = self.api.rate_limit_status()
            status = limits['resources']['statuses']['/statuses/update']
            self.logger.info("\n[RATE LIMITS]")
            self.logger.info(f"[-] Remaining posts: {status['remaining']}/{status['limit']}")
            self.logger.info(f"[-] Reset time: {status['reset']} seconds")
            return True
        except Exception as e:
            self.logger.warning(f"\n[WARNING] Unable to check rate limits: {str(e)}")
            return False