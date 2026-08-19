"""Watchlist monitoring service for tracking accounts and keywords."""

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.models.watchlist import WatchlistAccount, WatchlistKeyword, AccountMention
from app.services.x.client import XClient

logger = logging.getLogger(__name__)


class WatchlistMonitor:
    """Service for monitoring watchlist accounts and keywords."""

    def __init__(self, db: Session, x_client: XClient):
        self.db = db
        self.x_client = x_client

    async def monitor_accounts(
        self,
        limit: int = 50
    ) -> int:
        """
        Monitor all active watchlist accounts for new tweets.
        
        Args:
            limit: Maximum number of accounts to process
            
        Returns:
            Number of new mentions recorded
        """
        # Get active watchlist accounts
        accounts = self.db.query(WatchlistAccount).filter(
            WatchlistAccount.is_active == True
        ).limit(limit).all()
        
        total_mentions = 0
        
        for account in accounts:
            try:
                mentions_count = await self._monitor_single_account(account)
                total_mentions += mentions_count
            except Exception as e:
                logger.error(f"Error monitoring account {account.username}: {e}")
        
        logger.info(f"Monitored {len(accounts)} accounts, found {total_mentions} new mentions")
        return total_mentions

    async def _monitor_single_account(
        self,
        account: WatchlistAccount
    ) -> int:
        """
        Monitor a single account for new tweets.
        
        Args:
            account: WatchlistAccount object
            
        Returns:
            Number of new mentions recorded
        """
        # Get last check time
        last_check = account.last_checked_at or (datetime.utcnow() - timedelta(hours=1))
        
        # Fetch recent tweets from the account
        tweets = await self.x_client.get_user_tweets(
            username=account.username,
            since_id=account.last_tweet_id,
            max_results=10
        )
        
        new_mentions = 0
        
        for tweet in tweets:
            # Check if we already have this tweet
            existing = self.db.query(AccountMention).filter(
                AccountMention.tweet_id == tweet["id"]
            ).first()
            
            if existing:
                continue
            
            # Create new mention record
            mention = AccountMention(
                account_id=account.id,
                tweet_id=tweet["id"],
                text=tweet.get("text", ""),
                created_at=datetime.fromisoformat(tweet["created_at"].replace('Z', '+00:00')) if tweet.get("created_at") else datetime.utcnow(),
                retweet_count=tweet.get("public_metrics", {}).get("retweet_count", 0),
                like_count=tweet.get("public_metrics", {}).get("like_count", 0),
                reply_count=tweet.get("public_metrics", {}).get("reply_count", 0),
                quote_count=tweet.get("public_metrics", {}).get("quote_count", 0),
                is_retweet=tweet.get("referenced_types", ["tweet"])[0] == "retweeted",
                engagement_score=0.0  # Will be calculated
            )
            
            # Calculate engagement score
            mention.engagement_score = self._calculate_engagement_score(mention)
            
            self.db.add(mention)
            new_mentions += 1
            
            # Update account's last tweet info
            account.last_tweet_id = tweet["id"]
            account.last_checked_at = datetime.utcnow()
        
        if new_mentions > 0:
            self.db.commit()
        
        return new_mentions

    def _calculate_engagement_score(
        self,
        mention: AccountMention
    ) -> float:
        """
        Calculate engagement score for a mention.
        
        Formula: (likes * 1 + retweets * 1.5 + replies * 2 + quotes * 2) / 100
        
        Args:
            mention: AccountMention object
            
        Returns:
            Engagement score (0-100+)
        """
        score = (
            mention.like_count * 1.0 +
            mention.retweet_count * 1.5 +
            mention.reply_count * 2.0 +
            mention.quote_count * 2.0
        ) / 100.0
        
        return min(score, 100.0)  # Cap at 100

    async def monitor_keywords(
        self,
        limit: int = 50
    ) -> int:
        """
        Monitor all active watchlist keywords for new mentions.
        
        Args:
            limit: Maximum number of keywords to process
            
        Returns:
            Number of new mentions found
        """
        # Get active watchlist keywords
        keywords = self.db.query(WatchlistKeyword).filter(
            WatchlistKeyword.is_active == True
        ).limit(limit).all()
        
        total_mentions = 0
        
        for keyword in keywords:
            try:
                mentions_count = await self._monitor_single_keyword(keyword)
                total_mentions += mentions_count
            except Exception as e:
                logger.error(f"Error monitoring keyword {keyword.keyword}: {e}")
        
        logger.info(f"Monitored {len(keywords)} keywords, found {total_mentions} new mentions")
        return total_mentions

    async def _monitor_single_keyword(
        self,
        keyword: WatchlistKeyword
    ) -> int:
        """
        Monitor a single keyword for new mentions.
        
        Args:
            keyword: WatchlistKeyword object
            
        Returns:
            Number of new mentions found
        """
        # Get last check time
        last_check = keyword.last_checked_at or (datetime.utcnow() - timedelta(hours=1))
        
        # Search for recent tweets with this keyword
        query = f"{keyword.keyword} since:{last_check.strftime('%Y-%m-%d')}"
        
        if keyword.language:
            query += f" lang:{keyword.language}"
        
        tweets = await self.x_client.search_tweets(
            query=query,
            max_results=10,
            sort_order="recency"
        )
        
        # Note: In a real implementation, we would save these mentions
        # For now, just update the last checked time
        keyword.last_checked_at = datetime.utcnow()
        self.db.commit()
        
        return len(tweets)

    def add_account_to_watchlist(
        self,
        username: str,
        category: str = "competitor",
        notes: Optional[str] = None
    ) -> WatchlistAccount:
        """
        Add an account to the watchlist.
        
        Args:
            username: Twitter/X username (without @)
            category: Account category
            notes: Optional notes about the account
            
        Returns:
            Created WatchlistAccount object
        """
        # Check if already exists
        existing = self.db.query(WatchlistAccount).filter(
            WatchlistAccount.username == username
        ).first()
        
        if existing:
            logger.warning(f"Account {username} already in watchlist")
            return existing
        
        # Create new account
        account = WatchlistAccount(
            username=username,
            category=category,
            notes=notes,
            is_active=True
        )
        
        self.db.add(account)
        self.db.commit()
        self.db.refresh(account)
        
        logger.info(f"Added {username} to watchlist ({category})")
        return account

    def add_keyword_to_watchlist(
        self,
        keyword: str,
        category: str = "industry",
        language: str = "en",
        notes: Optional[str] = None
    ) -> WatchlistKeyword:
        """
        Add a keyword to the watchlist.
        
        Args:
            keyword: Keyword or hashtag to monitor
            category: Keyword category
            language: Language code
            notes: Optional notes
            
        Returns:
            Created WatchlistKeyword object
        """
        # Check if already exists
        existing = self.db.query(WatchlistKeyword).filter(
            WatchlistKeyword.keyword == keyword
        ).first()
        
        if existing:
            logger.warning(f"Keyword '{keyword}' already in watchlist")
            return existing
        
        # Create new keyword
        kw = WatchlistKeyword(
            keyword=keyword,
            category=category,
            language=language,
            notes=notes,
            is_active=True
        )
        
        self.db.add(kw)
        self.db.commit()
        self.db.refresh(kw)
        
        logger.info(f"Added keyword '{keyword}' to watchlist ({category})")
        return kw

    def get_recent_mentions(
        self,
        account_id: Optional[int] = None,
        limit: int = 50,
        min_engagement: float = 0.0
    ) -> List[AccountMention]:
        """
        Get recent mentions from watchlist accounts.
        
        Args:
            account_id: Filter by specific account
            limit: Maximum number of mentions to return
            min_engagement: Minimum engagement score
            
        Returns:
            List of AccountMention objects
        """
        query = self.db.query(AccountMention).filter(
            AccountMention.engagement_score >= min_engagement
        )
        
        if account_id:
            query = query.filter(AccountMention.account_id == account_id)
        
        return query.order_by(desc(AccountMention.created_at)).limit(limit).all()

    def get_high_engagement_mentions(
        self,
        hours: int = 24,
        min_score: float = 5.0
    ) -> List[AccountMention]:
        """
        Get high-engagement mentions from the specified time period.
        
        Args:
            hours: Number of hours to look back
            min_score: Minimum engagement score
            
        Returns:
            List of high-engagement mentions
        """
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        
        return self.db.query(AccountMention).filter(
            AccountMention.created_at > cutoff,
            AccountMention.engagement_score >= min_score
        ).order_by(desc(AccountMention.engagement_score)).all()
