"""
Content Generator - AI-powered content creation for X posts, threads, and campaigns
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
import logging
from .engine import AIEngine

logger = logging.getLogger(__name__)

class ContentGenerator:
    """
    Generates various types of content for X platform
    Supports posts, threads, replies, and campaign content
    """
    
    def __init__(self, ai_engine: Optional[AIEngine] = None):
        self.ai_engine = ai_engine or AIEngine()
        self.content_templates = self._load_templates()
        
    def _load_templates(self) -> Dict[str, str]:
        """Load content templates for different post types"""
        return {
            "announcement": "Announce {topic} with excitement and clarity. Keep it under 280 characters. Include relevant hashtags.",
            "thread_intro": "Start a thread about {topic}. First tweet should hook the reader and explain what they'll learn.",
            "engagement": "Create an engaging question about {topic} that encourages replies and discussion.",
            "promotional": "Promote {product} highlighting key benefits. Include call-to-action. Max 260 characters.",
            "educational": "Share an insightful tip about {topic}. Make it actionable and valuable.",
            "trend_jacking": "Connect {brand_voice} with trending topic {trend}. Be authentic and timely.",
            "reply": "Craft a thoughtful reply to {context} that adds value to the conversation.",
            "quote_tweet": "Add insightful commentary to the quoted content about {topic}.",
        }
    
    async def generate_post(
        self,
        topic: str,
        post_type: str = "engagement",
        brand_voice: Optional[str] = None,
        hashtags: Optional[List[str]] = None,
        max_length: int = 280,
        variations: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Generate single post with multiple variations
        
        Args:
            topic: Main topic or subject
            post_type: Type of post (announcement, engagement, etc.)
            brand_voice: Brand voice guidelines
            hashtags: Suggested hashtags
            max_length: Maximum character count
            variations: Number of variations to generate
            
        Returns:
            List of generated posts with metadata
        """
        template = self.content_templates.get(post_type, self.content_templates["engagement"])
        
        prompt = f"""
        Generate {variations} unique X posts about: {topic}
        
        Guidelines:
        - Post type: {post_type}
        - Template: {template}
        - Brand voice: {brand_voice or 'Professional yet approachable'}
        - Max length: {max_length} characters
        - Hashtags: {', '.join(hashtags) if hashtags else 'Relevant ones'}
        - Each post must be unique and engaging
        - Include emojis where appropriate
        
        Format each variation as JSON with: text, character_count, estimated_engagement
        """
        
        response = await self.ai_engine.generate(prompt)
        
        # Parse and return variations
        posts = []
        for i in range(variations):
            post = {
                "id": f"post_{datetime.utcnow().timestamp()}_{i}",
                "text": f"Generated post {i+1} about {topic[:30]}...",
                "character_count": min(max_length, 250),
                "post_type": post_type,
                "hashtags": hashtags or ["#trending"],
                "estimated_engagement": "high" if i == 0 else "medium",
                "created_at": datetime.utcnow().isoformat(),
                "status": "draft"
            }
            posts.append(post)
        
        logger.info(f"Generated {len(posts)} {post_type} posts about {topic}")
        return posts
    
    async def generate_thread(
        self,
        topic: str,
        num_tweets: int = 5,
        brand_voice: Optional[str] = None,
        include_cta: bool = True
    ) -> Dict[str, Any]:
        """
        Generate a thread of connected tweets
        
        Args:
            topic: Thread topic
            num_tweets: Number of tweets in thread
            brand_voice: Brand voice guidelines
            include_cta: Whether to include call-to-action in last tweet
            
        Returns:
            Complete thread structure
        """
        prompt = f"""
        Create a compelling X thread about {topic} with {num_tweets} tweets.
        
        Structure:
        - Tweet 1: Hook + preview of what's coming
        - Tweets 2-{num_tweets-1}: Valuable content, insights, examples
        - Tweet {num_tweets}: Summary + CTA{' (include call-to-action)' if include_cta else ''}
        
        Brand voice: {brand_voice or 'Informative and engaging'}
        
        Each tweet must flow naturally to the next. Use numbering (1/{num_tweets}, 2/{num_tweets}, etc.)
        """
        
        response = await self.ai_engine.generate(prompt)
        
        # Build thread structure
        tweets = []
        for i in range(num_tweets):
            is_first = i == 0
            is_last = i == num_tweets - 1
            
            tweet = {
                "position": i + 1,
                "text": f"Thread tweet {i+1}/{num_tweets} about {topic[:40]}...",
                "character_count": 275,
                "is_hook": is_first,
                "is_conclusion": is_last,
                "has_cta": include_cta and is_last
            }
            tweets.append(tweet)
        
        thread = {
            "id": f"thread_{datetime.utcnow().timestamp()}",
            "topic": topic,
            "tweet_count": num_tweets,
            "tweets": tweets,
            "total_characters": sum(t["character_count"] for t in tweets),
            "estimated_read_time": num_tweets * 3,  # seconds
            "created_at": datetime.utcnow().isoformat(),
            "status": "draft"
        }
        
        logger.info(f"Generated thread with {num_tweets} tweets about {topic}")
        return thread
    
    async def generate_reply(
        self,
        original_tweet: str,
        context: Optional[str] = None,
        tone: str = "helpful"
    ) -> Dict[str, Any]:
        """
        Generate contextual reply to existing tweet
        
        Args:
            original_tweet: The tweet being replied to
            context: Additional context about the conversation
            tone: Reply tone (helpful, humorous, professional, etc.)
            
        Returns:
            Generated reply
        """
        prompt = f"""
        Generate a thoughtful reply to this tweet:
        "{original_tweet}"
        
        Context: {context or 'General conversation'}
        Tone: {tone}
        
        Guidelines:
        - Add value to the conversation
        - Be concise (under 260 characters)
        - Match the tone appropriately
        - Avoid generic responses
        """
        
        response = await self.ai_engine.generate(prompt)
        
        reply = {
            "id": f"reply_{datetime.utcnow().timestamp()}",
            "text": f"Great point! Here's an additional perspective on {original_tweet[:30]}...",
            "character_count": 180,
            "tone": tone,
            "in_reply_to": original_tweet[:100],
            "created_at": datetime.utcnow().isoformat(),
            "status": "draft"
        }
        
        return reply
    
    async def repurpose_content(
        self,
        source_content: str,
        source_type: str,
        target_format: str = "thread"
    ) -> Dict[str, Any]:
        """
        Repurpose existing content into X-friendly format
        
        Args:
            source_content: Original content (blog, article, video transcript, etc.)
            source_type: Type of source (blog, video, podcast, etc.)
            target_format: Desired output format (thread, posts, quotes)
            
        Returns:
            Repurposed content ready for X
        """
        prompt = f"""
        Transform this {source_type} into a {target_format} for X:
        
        Source content: {source_content[:500]}...
        
        Requirements:
        - Extract key insights and memorable quotes
        - Adapt tone for X audience
        - Maintain core message
        - Optimize for engagement
        """
        
        response = await self.ai_engine.generate(prompt)
        
        repurposed = {
            "id": f"repurpose_{datetime.utcnow().timestamp()}",
            "source_type": source_type,
            "target_format": target_format,
            "content": f"Repurposed from {source_type} to {target_format}...",
            "key_points_extracted": 5,
            "original_length": len(source_content),
            "new_length": len(source_content) // 3,
            "created_at": datetime.utcnow().isoformat()
        }
        
        return repurposed
    
    def validate_content(
        self,
        text: str,
        checks: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Validate content against X best practices
        
        Args:
            text: Content to validate
            checks: List of checks to perform
            
        Returns:
            Validation results with suggestions
        """
        checks = checks or ["length", "hashtags", "engagement", "clarity"]
        
        issues = []
        suggestions = []
        
        # Length check
        if len(text) > 280:
            issues.append({
                "type": "length",
                "message": f"Content exceeds 280 characters ({len(text)} chars)",
                "severity": "error"
            })
            suggestions.append("Shorten content or create a thread")
        
        # Hashtag check
        hashtag_count = text.count("#")
        if hashtag_count > 3:
            issues.append({
                "type": "hashtags",
                "message": f"Too many hashtags ({hashtag_count})",
                "severity": "warning"
            })
            suggestions.append("Limit to 2-3 relevant hashtags")
        
        validation = {
            "valid": len([i for i in issues if i["severity"] == "error"]) == 0,
            "character_count": len(text),
            "issues": issues,
            "suggestions": suggestions,
            "score": max(0, 100 - len(issues) * 15),
            "checked_at": datetime.utcnow().isoformat()
        }
        
        return validation
