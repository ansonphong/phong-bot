import os
import logging
import tweepy
from typing import List, Optional
from post_base import BasePoster, PostContent
from tqdm import tqdm

class XPoster(BasePoster):
    def __init__(self, config: dict):
        """Initialize X/Twitter poster with configuration."""
        super().__init__(config)
        self.logger = logging.getLogger(__name__)
        self._init_client(config['x'])

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
        """Upload a video in chunks with progress bar."""
        try:
            file_size = os.path.getsize(video_path)
            print(f"\nUploading video: {os.path.basename(video_path)}")
            
            # INIT
            upload = self.api.chunked_upload(filename=video_path, file_size=file_size)
            
            # APPEND
            chunk_size = 1024 * 1024  # 1MB chunks
            total_chunks = (file_size + chunk_size - 1) // chunk_size
            
            with open(video_path, 'rb') as file, \
                tqdm(total=total_chunks, desc="Uploading", unit="MB") as pbar:
                
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
                    pbar.update(1)
            
            # FINALIZE
            print("Finalizing upload...")
            media = self.api.chunked_upload(media_id=upload.media_id, status='FINALIZE')
            
            print(f"Video upload complete! Media ID: {media.media_id}")
            return media.media_id
            
        except Exception as e:
            self.logger.error(f"Failed to upload video {video_path}: {str(e)}")
            print(f"Error uploading video: {str(e)}")
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to upload video {video_path}: {str(e)}")
            print(f"Error uploading video: {str(e)}")
            return None

    def _upload_image(self, image_path: str, alt_text: Optional[str] = None) -> Optional[int]:
        """Upload an image with progress bar."""
        try:
            file_size = os.path.getsize(image_path)
            print(f"\nUploading image: {os.path.basename(image_path)}")
            
            with tqdm(total=100, desc="Uploading", unit="%") as pbar:
                media = self.api.media_upload(filename=image_path)
                pbar.update(100)  # Since we can't get real-time progress for images
                
            if alt_text:
                print("Adding alt text...")
                self.api.create_media_metadata(media.media_id, alt_text)
                
            print(f"Image upload complete! Media ID: {media.media_id}")
            return media.media_id
            
        except Exception as e:
            self.logger.error(f"Failed to upload image {image_path}: {str(e)}")
            print(f"Error uploading image: {str(e)}")
            return None

    def post_content(self, post: PostContent) -> bool:
        """Post content to X/Twitter with progress feedback."""
        if not self.validate_post_content(post):
            print("Content validation failed")
            return False

        try:
            media_ids = []
            
            # Handle images if present
            if post.images:
                print(f"\nProcessing {len(post.images)} images...")
                for i, image in enumerate(post.images, 1):
                    print(f"\nImage {i}/{len(post.images)}")
                    if not self._validate_media_file(image):
                        print(f"Failed to validate image: {image}")
                        return False
                    
                    media_id = self._upload_image(image, post.alt_text)
                    if media_id:
                        media_ids.append(media_id)
                    else:
                        return False

            # Handle video if present
            elif post.video:
                print("\nProcessing video...")
                if not self._validate_media_file(post.video):
                    print(f"Failed to validate video: {post.video}")
                    return False
                
                media_id = self._upload_chunked_video(post.video)
                if media_id:
                    media_ids.append(media_id)
                else:
                    return False

            # Create the tweet
            print("\nPosting to X...")
            response = self.client.create_tweet(
                text=post.main_text if post.main_text else None,
                media_ids=media_ids if media_ids else None
            )
            
            if response and hasattr(response, 'data'):
                tweet_id = response.data['id']
                print(f"\nSuccess! Tweet posted with ID: {tweet_id}")
                self.logger.info(f"Successfully posted to X. Tweet ID: {tweet_id}")
                return True
            else:
                print("\nError: Failed to post to X - No response data received")
                return False

        except tweepy.TweepyException as e:
            print(f"\nError: Failed to post to X - {str(e)}")
            self.logger.error(f"Tweepy error while posting to X: {str(e)}")
            return False
        except Exception as e:
            print(f"\nError: Unexpected error while posting to X - {str(e)}")
            self.logger.error(f"Unexpected error while posting to X: {str(e)}")
            return False

    def _validate_rate_limits(self):
        """Check current rate limit status."""
        try:
            limits = self.api.rate_limit_status()
            status = limits['resources']['statuses']['/statuses/update']
            print(f"\nRate limits:")
            print(f"- Tweets remaining: {status['remaining']}/{status['limit']}")
            print(f"- Resets in: {status['reset']} seconds")
            return True
        except Exception as e:
            print(f"\nWarning: Failed to check rate limits - {str(e)}")
            return False