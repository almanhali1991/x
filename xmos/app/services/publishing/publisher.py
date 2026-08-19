"""Content publishing service for scheduling and posting content."""

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.models.content import Post, ContentStatus
from app.models.publishing import PublishLog, PublishingSchedule
from app.services.x.client import XClient

logger = logging.getLogger(__name__)


class ContentPublisher:
    """Service for publishing content to X."""

    def __init__(self, db: Session, x_client: XClient):
        self.db = db
        self.x_client = x_client

    async def publish_post(
        self,
        post_id: int,
        account_id: str
    ) -> Dict[str, Any]:
        """
        Publish a single post to X.
        
        Args:
            post_id: Post ID to publish
            account_id: X account ID to publish from
            
        Returns:
            Publishing result dictionary
        """
        # Get post from database
        post = self.db.query(Post).filter(Post.id == post_id).first()
        
        if not post:
            logger.error(f"Post {post_id} not found")
            return {"success": False, "error": "Post not found"}
        
        if post.status != "approved":
            logger.warning(f"Post {post_id} is not approved (status: {post.status})")
            return {"success": False, "error": f"Post not approved: {post.status}"}
        
        try:
            # Prepare media if exists
            media_ids = []
            if post.media_urls:
                for media_url in post.media_urls:
                    media_id = await self.x_client.upload_media(media_url)
                    if media_id:
                        media_ids.append(media_id)
            
            # Publish to X
            tweet_response = await self.x_client.post_tweet(
                text=post.content,
                media_ids=media_ids if media_ids else None,
                reply_to=None  # Will be set if part of thread
            )
            
            if tweet_response and "id" in tweet_response:
                # Update post status
                post.status = "published"
                post.published_at = datetime.utcnow()
                post.external_id = tweet_response["id"]
                
                # Create publish log
                log = PublishLog(
                    post_id=post_id,
                    status="success",
                    published_at=datetime.utcnow(),
                    external_id=tweet_response["id"],
                    external_url=f"https://x.com/status/{tweet_response['id']}",
                    error_message=None
                )
                
                self.db.add(log)
                self.db.commit()
                
                logger.info(f"Published post {post_id} to X: {tweet_response['id']}")
                
                return {
                    "success": True,
                    "post_id": post_id,
                    "tweet_id": tweet_response["id"],
                    "url": f"https://x.com/status/{tweet_response['id']}"
                }
            else:
                raise Exception("Invalid response from X API")
                
        except Exception as e:
            logger.error(f"Failed to publish post {post_id}: {e}")
            
            # Log failure
            log = PublishLog(
                post_id=post_id,
                status="failed",
                published_at=datetime.utcnow(),
                external_id=None,
                external_url=None,
                error_message=str(e)
            )
            
            self.db.add(log)
            post.status = "failed"
            self.db.commit()
            
            return {"success": False, "error": str(e)}

    async def publish_thread(
        self,
        thread_id: str,
        account_id: str
    ) -> Dict[str, Any]:
        """
        Publish a thread (series of connected posts) to X.
        
        Args:
            thread_id: Thread ID (parent post ID)
            account_id: X account ID to publish from
            
        Returns:
            Publishing result dictionary
        """
        # Get parent post
        parent_post = self.db.query(Post).filter(
            Post.id == int(thread_id)
        ).first()
        
        if not parent_post:
            logger.error(f"Thread parent post {thread_id} not found")
            return {"success": False, "error": "Thread not found"}
        
        # Get all posts in thread
        thread_posts = self.db.query(Post).filter(
            (Post.id == int(thread_id)) | (Post.thread_id == thread_id)
        ).order_by(Post.created_at).all()
        
        if not thread_posts:
            logger.error(f"No posts found for thread {thread_id}")
            return {"success": False, "error": "No posts in thread"}
        
        try:
            # Publish first tweet
            first_post = thread_posts[0]
            first_response = await self.x_client.post_tweet(
                text=first_post.content,
                media_ids=first_post.media_urls if hasattr(first_post, 'media_urls') else None
            )
            
            if not first_response or "id" not in first_response:
                raise Exception("Failed to publish first tweet")
            
            tweet_ids = [first_response["id"]]
            
            # Publish replies
            for i, post in enumerate(thread_posts[1:], start=1):
                reply_response = await self.x_client.post_tweet(
                    text=post.content,
                    media_ids=post.media_urls if hasattr(post, 'media_urls') else None,
                    reply_to=tweet_ids[-1]  # Reply to previous tweet
                )
                
                if reply_response and "id" in reply_response:
                    tweet_ids.append(reply_response["id"])
                    
                    # Update post status
                    post.status = "published"
                    post.published_at = datetime.utcnow()
                    post.external_id = reply_response["id"]
                else:
                    logger.warning(f"Failed to publish thread tweet {i}")
            
            # Update parent post
            parent_post.status = "published"
            parent_post.published_at = datetime.utcnow()
            parent_post.external_id = tweet_ids[0]
            
            # Create publish log
            log = PublishLog(
                post_id=parent_post.id,
                status="success",
                published_at=datetime.utcnow(),
                external_id=tweet_ids[0],
                external_url=f"https://x.com/status/{tweet_ids[0]}",
                error_message=None,
                metadata={"thread_tweet_ids": tweet_ids}
            )
            
            self.db.add(log)
            self.db.commit()
            
            logger.info(f"Published thread {thread_id} with {len(tweet_ids)} tweets")
            
            return {
                "success": True,
                "thread_id": thread_id,
                "tweet_ids": tweet_ids,
                "url": f"https://x.com/status/{tweet_ids[0]}"
            }
            
        except Exception as e:
            logger.error(f"Failed to publish thread {thread_id}: {e}")
            
            log = PublishLog(
                post_id=parent_post.id if parent_post else None,
                status="failed",
                published_at=datetime.utcnow(),
                external_id=None,
                external_url=None,
                error_message=str(e)
            )
            
            self.db.add(log)
            self.db.commit()
            
            return {"success": False, "error": str(e)}

    def schedule_post(
        self,
        post_id: int,
        scheduled_time: datetime,
        account_id: str
    ) -> PublishingSchedule:
        """
        Schedule a post for future publishing.
        
        Args:
            post_id: Post ID to schedule
            scheduled_time: When to publish
            account_id: X account ID
            
        Returns:
            Created PublishingSchedule object
        """
        # Check if post exists and is approved
        post = self.db.query(Post).filter(Post.id == post_id).first()
        
        if not post:
            raise ValueError(f"Post {post_id} not found")
        
        if post.status != "approved":
            raise ValueError(f"Post {post_id} is not approved")
        
        # Create schedule
        schedule = PublishingSchedule(
            post_id=post_id,
            scheduled_at=scheduled_time,
            account_id=account_id,
            status="scheduled"
        )
        
        self.db.add(schedule)
        self.db.commit()
        self.db.refresh(schedule)
        
        logger.info(f"Scheduled post {post_id} for {scheduled_time}")
        return schedule

    def get_scheduled_posts(
        self,
        account_id: Optional[str] = None,
        limit: int = 50
    ) -> List[PublishingSchedule]:
        """
        Get scheduled posts.
        
        Args:
            account_id: Filter by account
            limit: Maximum number to return
            
        Returns:
            List of PublishingSchedule objects
        """
        query = self.db.query(PublishingSchedule).filter(
            PublishingSchedule.status == "scheduled",
            PublishingSchedule.scheduled_at > datetime.utcnow()
        )
        
        if account_id:
            query = query.filter(PublishingSchedule.account_id == account_id)
        
        return query.order_by(PublishingSchedule.scheduled_at).limit(limit).all()

    async def publish_scheduled_posts(self) -> int:
        """
        Publish all posts that are due for publishing.
        
        Returns:
            Number of posts published
        """
        # Get due scheduled posts
        now = datetime.utcnow()
        due_schedules = self.db.query(PublishingSchedule).filter(
            PublishingSchedule.status == "scheduled",
            PublishingSchedule.scheduled_at <= now
        ).all()
        
        published_count = 0
        
        for schedule in due_schedules:
            result = await self.publish_post(
                post_id=schedule.post_id,
                account_id=schedule.account_id
            )
            
            if result.get("success"):
                schedule.status = "published"
                schedule.published_at = now
                published_count += 1
            else:
                schedule.status = "failed"
                schedule.error_message = result.get("error", "Unknown error")
        
        self.db.commit()
        
        logger.info(f"Published {published_count}/{len(due_schedules)} scheduled posts")
        return published_count

    def cancel_schedule(self, schedule_id: int) -> bool:
        """
        Cancel a scheduled post.
        
        Args:
            schedule_id: Schedule ID to cancel
            
        Returns:
            True if cancelled successfully
        """
        schedule = self.db.query(PublishingSchedule).filter(
            PublishingSchedule.id == schedule_id
        ).first()
        
        if not schedule:
            logger.error(f"Schedule {schedule_id} not found")
            return False
        
        if schedule.status != "scheduled":
            logger.warning(f"Schedule {schedule_id} is not in 'scheduled' status")
            return False
        
        schedule.status = "cancelled"
        self.db.commit()
        
        logger.info(f"Cancelled schedule {schedule_id}")
        return True

    def get_publish_history(
        self,
        post_id: Optional[int] = None,
        days: int = 30,
        limit: int = 100
    ) -> List[PublishLog]:
        """
        Get publishing history.
        
        Args:
            post_id: Filter by post
            days: Number of days to look back
            limit: Maximum number of records
            
        Returns:
            List of PublishLog objects
        """
        cutoff = datetime.utcnow() - timedelta(days=days)
        
        query = self.db.query(PublishLog).filter(
            PublishLog.published_at > cutoff
        )
        
        if post_id:
            query = query.filter(PublishLog.post_id == post_id)
        
        return query.order_by(desc(PublishLog.published_at)).limit(limit).all()
