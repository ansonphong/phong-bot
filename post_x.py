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

    def post_content(self, post: PostContent) -> bool:
        """Post content to X/Twitter. Extends BasePoster's post_content method."""
        # First validate the content using parent class method
        if not self.validate_post_content(post):
            self.logger.error("Content validation failed")
            return False

        try:
            media_ids = []

            # Handle images if present
            if post.images:
                for image in post.images:
                    if not self._validate_media_file(image):
                        self.logger.error(f"Failed to validate image: {image}")
                        return False
                    
                    try:
                        media = self.api.media_upload(filename=image)
                        if post.alt_text:
                            self.api.create_media_metadata(media.media_id, post.alt_text)
                        media_ids.append(media.media_id)
                        self.logger.info(f"Successfully uploaded image: {image}")
                    except Exception as e:
                        self.logger.error(f"Failed to upload image {image}: {str(e)}")
                        return False

            # Handle video if present
            elif post.video:
                if not self._validate_media_file(post.video):
                    self.logger.error(f"Failed to validate video: {post.video}")
                    return False
                    
                try:
                    media = self.api.media_upload(
                        filename=post.video,
                        chunked=True  # Use chunked upload for videos
                    )
                    if post.alt_text:
                        self.api.create_media_metadata(media.media_id, post.alt_text)
                    media_ids.append(media.media_id)
                    self.logger.info(f"Successfully uploaded video: {post.video}")
                except Exception as e:
                    self.logger.error(f"Failed to upload video {post.video}: {str(e)}")
                    return False

            # Create the tweet
            response = self.client.create_tweet(
                text=post.main_text if post.main_text else None,
                media_ids=media_ids if media_ids else None
            )
            
            if response and hasattr(response, 'data'):
                tweet_id = response.data['id']
                self.logger.info(f"Successfully posted to X. Tweet ID: {tweet_id}")
                return True
            else:
                self.logger.error("Failed to post to X: No response data received")
                return False

        except tweepy.TweepyException as e:
            self.logger.error(f"Tweepy error while posting to X: {str(e)}")
            return False
        except Exception as e:
            self.logger.error(f"Unexpected error while posting to X: {str(e)}")
            return False

    def _validate_rate_limits(self):
        """Check current rate limit status."""
        try:
            limits = self.api.rate_limit_status()
            # Log remaining tweet and media upload limits
            self.logger.info(f"Rate limits remaining: {limits['resources']['statuses']['/statuses/update']}")
            return True
        except Exception as e:
            self.logger.warning(f"Failed to check rate limits: {str(e)}")
            return False