import os
import random
import logging
from pathlib import Path
from typing import List, Optional, Dict, Set
from dataclasses import dataclass
import tweepy
from dotenv import load_dotenv

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

class TwitterAutoPoster:
    def __init__(self, posts_dir: str = "posts"):
        """Initialize the Twitter Auto Poster with configuration and authentication."""
        load_dotenv()  # Load environment variables from .env file
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('twitter_poster.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
        # Initialize paths
        self.posts_dir = Path(posts_dir)
        self.posted_file = self.posts_dir / "posted.txt"
        
        # Ensure directories exist
        self.posts_dir.mkdir(exist_ok=True)
        
        # Initialize Twitter API client
        self._init_twitter_client()
        
    def _init_twitter_client(self):
        """Initialize Twitter API client with credentials from environment variables."""
        try:
            # Debug log the credentials (remove in production!)
            self.logger.info("API Key exists: " + str(bool(os.getenv("TWITTER_API_KEY"))))
            self.logger.info("API Secret exists: " + str(bool(os.getenv("TWITTER_API_SECRET"))))
            self.logger.info("Access Token exists: " + str(bool(os.getenv("TWITTER_ACCESS_TOKEN"))))
            self.logger.info("Access Token Secret exists: " + str(bool(os.getenv("TWITTER_ACCESS_TOKEN_SECRET"))))
            self.logger.info("Bearer Token exists: " + str(bool(os.getenv("TWITTER_BEARER_TOKEN"))))
            
            auth = tweepy.OAuthHandler(
                os.getenv("TWITTER_API_KEY"),
                os.getenv("TWITTER_API_SECRET")
            )
            auth.set_access_token(
                os.getenv("TWITTER_ACCESS_TOKEN"),
                os.getenv("TWITTER_ACCESS_TOKEN_SECRET")
            )
            
            # Initialize v2 client with both OAuth 1.0a and Bearer Token
            self.client = tweepy.Client(
                bearer_token=os.getenv("TWITTER_BEARER_TOKEN"),
                consumer_key=os.getenv("TWITTER_API_KEY"),
                consumer_secret=os.getenv("TWITTER_API_SECRET"),
                access_token=os.getenv("TWITTER_ACCESS_TOKEN"),
                access_token_secret=os.getenv("TWITTER_ACCESS_TOKEN_SECRET"),
                wait_on_rate_limit=True
            )
            
            # Keep v1.1 API for media uploads
            self.api = tweepy.API(auth)
            
            # Test authentication
            try:
                self.api.verify_credentials()
                self.logger.info("Authentication Successful")
            except Exception as e:
                self.logger.error(f"Authentication Failed: {str(e)}")
                raise
                
        except Exception as e:
            self.logger.error(f"Failed to initialize Twitter client: {str(e)}")
            raise

    def _validate_media_file(self, filepath: str) -> bool:
        """Validate media file before upload."""
        try:
            file_size = os.path.getsize(filepath)
            # Twitter image size limit is 5MB
            max_size = 5 * 1024 * 1024  # 5MB in bytes
            
            if file_size > max_size:
                self.logger.error(f"File {filepath} exceeds 5MB limit: {file_size} bytes")
                return False
                
            self.logger.info(f"File {filepath} size: {file_size} bytes")
            return True
        except Exception as e:
            self.logger.error(f"Error validating file {filepath}: {str(e)}")
            return False

    def _get_posted_basenames(self) -> Set[str]:
        """Read and return set of already posted basenames."""
        if not self.posted_file.exists():
            return set()
        
        with open(self.posted_file, 'r') as f:
            return {line.strip() for line in f if line.strip()}

    def _get_basename_without_number(self, filename: str) -> str:
        """Extract basename without number suffix and extension."""
        base = Path(filename).stem
        # Remove -1, -2, etc. from the end if present
        if '-' in base:
            parts = base.rsplit('-', 1)
            if parts[1].isdigit():
                return parts[0]
        return base

    def _get_available_posts(self) -> List[str]:
        """Get list of available unique basenames that haven't been posted."""
        all_files = {f.name for f in self.posts_dir.iterdir() if f.is_file()}
        posted_basenames = self._get_posted_basenames()
        
        # Get unique basenames without numbers
        unique_basenames = {
            self._get_basename_without_number(f)
            for f in all_files
            if not f.startswith('.') and f != 'posted.txt'
        }
        
        # Remove already posted basenames
        available_posts = unique_basenames - posted_basenames
        return list(available_posts)

    def _build_post_content(self, basename: str) -> PostContent:
        """Build post content object from files matching basename."""
        post = PostContent(basename=basename)
        
        # Find all related files
        files = list(self.posts_dir.glob(f"{basename}*"))
        
        for file in files:
            # Replace spaces with underscores in filenames
            if ' ' in str(file):
                new_name = str(file).replace(' ', '_')
                os.rename(str(file), new_name)
                file = Path(new_name)
                
            suffix = file.suffix.lower()
            stem = file.stem
            
            # Handle text content
            if suffix == '.txt':
                with open(file, 'r', encoding='utf-8') as f:
                    if stem.endswith('-alt'):
                        post.alt_text = f.read().strip()
                    else:
                        post.main_text = f.read().strip()
            
            # Handle images
            elif suffix in {'.jpg', '.jpeg', '.png', '.gif'}:
                post.images.append(str(file))
                post.images.sort()  # Ensure consistent order
            
            # Handle videos
            elif suffix in {'.mp4', '.mov'}:
                post.video = str(file)
        
        return post

    def _post_to_twitter(self, post: PostContent) -> bool:
        """Post content to Twitter using Tweepy."""
        try:
            media_ids = []
            
            # Handle images
            if post.images:
                for image in post.images:
                    if not self._validate_media_file(image):
                        continue
                    
                    try:
                        self.logger.info(f"Attempting to upload: {image}")
                        with open(image, 'rb') as media_file:
                            media = self.api.media_upload(filename=image, file=media_file)
                            self.logger.info(f"Media upload response: {media}")
                            
                            if post.alt_text:
                                try:
                                    self.api.create_media_metadata(media.media_id, post.alt_text)
                                    self.logger.info(f"Added alt text to media {media.media_id}")
                                except Exception as alt_error:
                                    self.logger.error(f"Failed to add alt text: {str(alt_error)}")
                                    
                            media_ids.append(media.media_id)
                            self.logger.info(f"Successfully uploaded media: {image} with ID: {media.media_id}")
                            
                    except Exception as e:
                        self.logger.error(f"Failed to upload media {image}: {str(e)}")
                        self.logger.error(f"Full error details: {repr(e)}")
                        raise
            
            # Handle video
            elif post.video:
                if not self._validate_media_file(post.video):
                    return False
                    
                try:
                    self.logger.info(f"Attempting to upload video: {post.video}")
                    with open(post.video, 'rb') as video_file:
                        media = self.api.media_upload(
                            filename=post.video,
                            file=video_file,
                            media_type='video/mp4'
                        )
                        
                        if post.alt_text:
                            try:
                                self.api.create_media_metadata(media.media_id, post.alt_text)
                                self.logger.info(f"Added alt text to video {media.media_id}")
                            except Exception as alt_error:
                                self.logger.error(f"Failed to add alt text to video: {str(alt_error)}")
                                
                        media_ids.append(media.media_id)
                        self.logger.info(f"Successfully uploaded video: {post.video} with ID: {media.media_id}")
                        
                except Exception as e:
                    self.logger.error(f"Failed to upload video {post.video}: {str(e)}")
                    self.logger.error(f"Full error details: {repr(e)}")
                    raise
            
            # Add debug logging
            self.logger.info(f"Attempting to post tweet with:")
            self.logger.info(f"- Text: {post.main_text}")
            self.logger.info(f"- Media IDs: {media_ids}")
            
            # Post to Twitter
            try:
                response = self.client.create_tweet(
                    text=post.main_text if post.main_text else None,
                    media_ids=media_ids if media_ids else None
                )
                
                self.logger.info(f"Tweet posted successfully: {response}")
                return True
                
            except Exception as e:
                self.logger.error(f"Failed to create tweet: {str(e)}")
                self.logger.error(f"Full error details: {repr(e)}")
                return False
                
        except tweepy.errors.Forbidden as e:
            self.logger.error(f"403 Forbidden error: {str(e)}")
            self.logger.error(f"Full error details: {repr(e)}")
            return False
        except Exception as e:
            self.logger.error(f"Failed to post to Twitter: {str(e)}")
            self.logger.error(f"Full error details: {repr(e)}")
            return False

    def _mark_as_posted(self, basename: str):
        """Mark basename as posted by adding to posted.txt."""
        with open(self.posted_file, 'a') as f:
            f.write(f"{basename}\n")

    def post_random_content(self) -> bool:
        """Main method to post random content to Twitter."""
        try:
            # Get available posts
            available_posts = self._get_available_posts()
            
            if not available_posts:
                self.logger.info("No new content available to post")
                return False
            
            # Select random post
            selected_basename = random.choice(available_posts)
            
            # Build post content
            post_content = self._build_post_content(selected_basename)
            
            # Post to Twitter
            if self._post_to_twitter(post_content):
                self._mark_as_posted(selected_basename)
                self.logger.info(f"Successfully posted content: {selected_basename}")
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error in post_random_content: {e}")
            return False

if __name__ == "__main__":
    # Create and run poster
    poster = TwitterAutoPoster()
    poster.post_random_content()