"""Content generation service for creating marketing content."""

import logging
from datetime import datetime
from typing import List, Dict, Any, Optional

from sqlalchemy.orm import Session

from app.models.content import Post, ContentCategory, ContentStatus
from app.models.brand import Brand, BrandVoice
from app.services.ai.content_generator import ContentGenerator as AIContentGenerator

logger = logging.getLogger(__name__)


class ContentGenerator:
    """Service for generating marketing content."""

    def __init__(self, db: Session, ai_generator: AIContentGenerator):
        self.db = db
        self.ai_generator = ai_generator

    async def generate_post(
        self,
        brand_id: int,
        topic: str,
        category: str = "general",
        tone: Optional[str] = None,
        include_hashtags: bool = True,
        variations: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Generate social media posts for a brand.
        
        Args:
            brand_id: Brand ID
            topic: Topic for the post
            category: Content category
            tone: Override tone (uses brand voice if not provided)
            include_hashtags: Whether to include hashtags
            variations: Number of variations to generate
            
        Returns:
            List of generated post dictionaries
        """
        # Get brand and voice
        brand = self.db.query(Brand).filter(Brand.id == brand_id).first()
        if not brand:
            logger.error(f"Brand {brand_id} not found")
            return []
        
        brand_voice = self.db.query(BrandVoice).filter(
            BrandVoice.brand_id == brand_id
        ).first()
        
        # Use brand tone if not specified
        if not tone and brand_voice:
            tone = brand_voice.tone
        
        # Generate content using AI
        posts_data = await self.ai_generator.generate_posts(
            topic=topic,
            brand_voice=brand_voice,
            tone=tone,
            include_hashtags=include_hashtags,
            variations=variations
        )
        
        # Add metadata
        for post_data in posts_data:
            post_data["brand_id"] = brand_id
            post_data["category"] = category
            post_data["status"] = "draft"
        
        logger.info(f"Generated {len(posts_data)} post variations for topic: {topic}")
        return posts_data

    async def generate_thread(
        self,
        brand_id: int,
        topic: str,
        num_tweets: int = 5,
        category: str = "thread"
    ) -> Dict[str, Any]:
        """
        Generate a thread (series of connected tweets).
        
        Args:
            brand_id: Brand ID
            topic: Thread topic
            num_tweets: Number of tweets in the thread
            category: Content category
            
        Returns:
            Thread dictionary with tweets list
        """
        # Get brand voice
        brand_voice = self.db.query(BrandVoice).filter(
            BrandVoice.brand_id == brand_id
        ).first()
        
        # Generate thread using AI
        thread_data = await self.ai_generator.generate_thread(
            topic=topic,
            brand_voice=brand_voice,
            num_tweets=num_tweets
        )
        
        # Add metadata
        thread_data["brand_id"] = brand_id
        thread_data["category"] = category
        thread_data["status"] = "draft"
        thread_data["created_at"] = datetime.utcnow()
        
        logger.info(f"Generated thread with {num_tweets} tweets on topic: {topic}")
        return thread_data

    async def generate_reply(
        self,
        brand_id: int,
        original_tweet: str,
        context: Optional[str] = None,
        tone: Optional[str] = None
    ) -> str:
        """
        Generate a reply to a tweet.
        
        Args:
            brand_id: Brand ID
            original_tweet: Text of the original tweet
            context: Additional context
            tone: Reply tone
            
        Returns:
            Generated reply text
        """
        # Get brand voice
        brand_voice = self.db.query(BrandVoice).filter(
            BrandVoice.brand_id == brand_id
        ).first()
        
        # Generate reply using AI
        reply = await self.ai_generator.generate_reply(
            original_tweet=original_tweet,
            brand_voice=brand_voice,
            context=context,
            tone=tone
        )
        
        logger.debug(f"Generated reply for brand {brand_id}")
        return reply

    async def repurpose_content(
        self,
        brand_id: int,
        source_content: str,
        source_type: str = "blog",
        target_format: str = "tweet",
        variations: int = 3
    ) -> List[str]:
        """
        Repurpose existing content into social media posts.
        
        Args:
            brand_id: Brand ID
            source_content: Original content text
            source_type: Type of source (blog, article, video, etc.)
            target_format: Target format (tweet, thread, linkedin, etc.)
            variations: Number of variations to generate
            
        Returns:
            List of repurposed content strings
        """
        # Get brand voice
        brand_voice = self.db.query(BrandVoice).filter(
            BrandVoice.brand_id == brand_id
        ).first()
        
        # Repurpose using AI
        repurposed = await self.ai_generator.repurpose_content(
            source_content=source_content,
            source_type=source_type,
            target_format=target_format,
            brand_voice=brand_voice,
            variations=variations
        )
        
        logger.info(
            f"Repurposed {source_type} content into {len(repurposed)} "
            f"{target_format} variations"
        )
        return repurposed

    def save_post(
        self,
        brand_id: int,
        content: str,
        category: str = "general",
        status: str = "draft",
        scheduled_at: Optional[datetime] = None,
        hashtags: Optional[List[str]] = None,
        media_urls: Optional[List[str]] = None,
        thread_id: Optional[str] = None
    ) -> Post:
        """
        Save a post to the database.
        
        Args:
            brand_id: Brand ID
            content: Post content
            category: Content category
            status: Post status
            scheduled_at: Scheduled publish time
            hashtags: List of hashtags
            media_urls: List of media URLs
            thread_id: Parent thread ID
            
        Returns:
            Saved Post object
        """
        post = Post(
            brand_id=brand_id,
            content=content,
            category=category,
            status=status,
            scheduled_at=scheduled_at,
            hashtags=hashtags or [],
            media_urls=media_urls or [],
            thread_id=thread_id,
            created_at=datetime.utcnow()
        )
        
        self.db.add(post)
        self.db.commit()
        self.db.refresh(post)
        
        logger.info(f"Saved post {post.id} for brand {brand_id}")
        return post

    def save_thread(
        self,
        brand_id: int,
        tweets: List[str],
        category: str = "thread",
        status: str = "draft"
    ) -> Dict[str, Any]:
        """
        Save a thread to the database.
        
        Args:
            brand_id: Brand ID
            tweets: List of tweet texts
            category: Content category
            status: Thread status
            
        Returns:
            Dictionary with thread info and saved posts
        """
        # Create parent thread record (using first post as reference)
        parent_post = self.save_post(
            brand_id=brand_id,
            content=tweets[0],
            category=category,
            status=status
        )
        
        saved_posts = [parent_post]
        
        # Create remaining tweets as part of thread
        for i, tweet_text in enumerate(tweets[1:], start=2):
            child_post = self.save_post(
                brand_id=brand_id,
                content=tweet_text,
                category=category,
                status=status,
                thread_id=str(parent_post.id)
            )
            saved_posts.append(child_post)
        
        logger.info(f"Saved thread with {len(saved_posts)} posts for brand {brand_id}")
        
        return {
            "id": parent_post.id,
            "brand_id": brand_id,
            "tweets": tweets,
            "posts": saved_posts,
            "created_at": parent_post.created_at
        }

    def get_draft_posts(
        self,
        brand_id: Optional[int] = None,
        category: Optional[str] = None,
        limit: int = 50
    ) -> List[Post]:
        """
        Get draft posts.
        
        Args:
            brand_id: Filter by brand
            category: Filter by category
            limit: Maximum number of posts to return
            
        Returns:
            List of Post objects
        """
        query = self.db.query(Post).filter(Post.status == "draft")
        
        if brand_id:
            query = query.filter(Post.brand_id == brand_id)
        
        if category:
            query = query.filter(Post.category == category)
        
        return query.order_by(Post.created_at.desc()).limit(limit).all()

    def approve_post(self, post_id: int) -> Optional[Post]:
        """
        Approve a draft post for publishing.
        
        Args:
            post_id: Post ID
            
        Returns:
            Updated Post object or None
        """
        post = self.db.query(Post).filter(Post.id == post_id).first()
        
        if not post:
            logger.error(f"Post {post_id} not found")
            return None
        
        post.status = "approved"
        post.approved_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(post)
        
        logger.info(f"Approved post {post_id}")
        return post

    def reject_post(self, post_id: int, reason: str) -> Optional[Post]:
        """
        Reject a draft post.
        
        Args:
            post_id: Post ID
            reason: Rejection reason
            
        Returns:
            Updated Post object or None
        """
        post = self.db.query(Post).filter(Post.id == post_id).first()
        
        if not post:
            logger.error(f"Post {post_id} not found")
            return None
        
        post.status = "rejected"
        post.rejection_reason = reason
        post.rejected_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(post)
        
        logger.info(f"Rejected post {post_id}: {reason}")
        return post
