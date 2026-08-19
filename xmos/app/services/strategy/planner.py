"""Strategy planning service for marketing strategy development."""

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

from sqlalchemy.orm import Session

from app.models.strategy import StrategicPlan, ContentPillar, CampaignMetrics
from app.models.brand import Brand, BrandVoice, TargetAudience
from app.services.ai.strategy_analyzer import StrategyAnalyzer as AIStrategyAnalyzer

logger = logging.getLogger(__name__)


class StrategyPlanner:
    """Service for planning and managing marketing strategies."""

    def __init__(self, db: Session, ai_analyzer: AIStrategyAnalyzer):
        self.db = db
        self.ai_analyzer = ai_analyzer

    async def create_strategic_plan(
        self,
        brand_id: int,
        plan_name: str,
        duration_months: int = 3,
        goals: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Create a comprehensive strategic plan for a brand.
        
        Args:
            brand_id: Brand ID
            plan_name: Name of the strategic plan
            duration_months: Plan duration in months
            goals: List of strategic goals
            
        Returns:
            Strategic plan dictionary
        """
        # Get brand information
        brand = self.db.query(Brand).filter(Brand.id == brand_id).first()
        if not brand:
            logger.error(f"Brand {brand_id} not found")
            return {}
        
        brand_voice = self.db.query(BrandVoice).filter(
            BrandVoice.brand_id == brand_id
        ).first()
        
        target_audiences = self.db.query(TargetAudience).filter(
            TargetAudience.brand_id == brand_id
        ).all()
        
        # Use AI to generate strategic plan
        plan_data = await self.ai_analyzer.create_strategic_plan(
            brand=brand,
            brand_voice=brand_voice,
            target_audiences=target_audiences,
            plan_name=plan_name,
            duration_months=duration_months,
            goals=goals
        )
        
        # Save strategic plan to database
        strategic_plan = StrategicPlan(
            brand_id=brand_id,
            plan_name=plan_name,
            start_date=datetime.utcnow(),
            end_date=datetime.utcnow() + timedelta(days=duration_months * 30),
            goals=goals or [],
            swot_analysis=plan_data.get("swot", {}),
            recommendations=plan_data.get("recommendations", []),
            status="active"
        )
        
        self.db.add(strategic_plan)
        self.db.commit()
        self.db.refresh(strategic_plan)
        
        # Create content pillars
        content_pillars = plan_data.get("content_pillars", [])
        for pillar_data in content_pillars:
            pillar = ContentPillar(
                plan_id=strategic_plan.id,
                name=pillar_data.get("name", ""),
                description=pillar_data.get("description", ""),
                themes=pillar_data.get("themes", []),
                priority=pillar_data.get("priority", "medium")
            )
            self.db.add(pillar)
        
        self.db.commit()
        
        logger.info(f"Created strategic plan '{plan_name}' for brand {brand_id}")
        
        return {
            "id": strategic_plan.id,
            "plan_name": plan_name,
            "brand_id": brand_id,
            "duration_months": duration_months,
            "content_pillars": len(content_pillars),
            "goals": goals
        }

    def add_content_pillar(
        self,
        plan_id: int,
        name: str,
        description: str,
        themes: List[str],
        priority: str = "medium"
    ) -> ContentPillar:
        """
        Add a content pillar to a strategic plan.
        
        Args:
            plan_id: Strategic plan ID
            name: Pillar name
            description: Pillar description
            themes: List of content themes
            priority: Priority level (low, medium, high)
            
        Returns:
            Created ContentPillar object
        """
        pillar = ContentPillar(
            plan_id=plan_id,
            name=name,
            description=description,
            themes=themes,
            priority=priority
        )
        
        self.db.add(pillar)
        self.db.commit()
        self.db.refresh(pillar)
        
        logger.info(f"Added content pillar '{name}' to plan {plan_id}")
        return pillar

    def get_strategic_plan(self, plan_id: int) -> Optional[Dict[str, Any]]:
        """
        Get a strategic plan with all details.
        
        Args:
            plan_id: Plan ID
            
        Returns:
            Plan dictionary or None
        """
        plan = self.db.query(StrategicPlan).filter(
            StrategicPlan.id == plan_id
        ).first()
        
        if not plan:
            return None
        
        # Get content pillars
        pillars = self.db.query(ContentPillar).filter(
            ContentPillar.plan_id == plan_id
        ).all()
        
        return {
            "id": plan.id,
            "plan_name": plan.plan_name,
            "brand_id": plan.brand_id,
            "start_date": plan.start_date,
            "end_date": plan.end_date,
            "goals": plan.goals,
            "swot_analysis": plan.swot_analysis,
            "recommendations": plan.recommendations,
            "status": plan.status,
            "content_pillars": [
                {
                    "id": p.id,
                    "name": p.name,
                    "description": p.description,
                    "themes": p.themes,
                    "priority": p.priority
                }
                for p in pillars
            ]
        }

    def update_plan_status(
        self,
        plan_id: int,
        status: str
    ) -> Optional[StrategicPlan]:
        """
        Update the status of a strategic plan.
        
        Args:
            plan_id: Plan ID
            status: New status (active, completed, archived)
            
        Returns:
            Updated StrategicPlan or None
        """
        plan = self.db.query(StrategicPlan).filter(
            StrategicPlan.id == plan_id
        ).first()
        
        if not plan:
            logger.error(f"Plan {plan_id} not found")
            return None
        
        plan.status = status
        self.db.commit()
        self.db.refresh(plan)
        
        logger.info(f"Updated plan {plan_id} status to {status}")
        return plan

    def get_active_plans(self, brand_id: Optional[int] = None) -> List[StrategicPlan]:
        """
        Get all active strategic plans.
        
        Args:
            brand_id: Optional brand filter
            
        Returns:
            List of StrategicPlan objects
        """
        query = self.db.query(StrategicPlan).filter(
            StrategicPlan.status == "active"
        )
        
        if brand_id:
            query = query.filter(StrategicPlan.brand_id == brand_id)
        
        return query.all()

    async def analyze_competitors(
        self,
        brand_id: int,
        competitor_accounts: List[str]
    ) -> Dict[str, Any]:
        """
        Analyze competitors and provide insights.
        
        Args:
            brand_id: Brand ID
            competitor_accounts: List of competitor X accounts
            
        Returns:
            Competitor analysis dictionary
        """
        # Get brand voice for context
        brand_voice = self.db.query(BrandVoice).filter(
            BrandVoice.brand_id == brand_id
        ).first()
        
        # Use AI to analyze competitors
        analysis = await self.ai_analyzer.analyze_competitors(
            competitor_accounts=competitor_accounts,
            brand_voice=brand_voice
        )
        
        logger.info(f"Analyzed {len(competitor_accounts)} competitors for brand {brand_id}")
        return analysis

    async def generate_campaign_strategy(
        self,
        brand_id: int,
        campaign_name: str,
        objective: str,
        duration_days: int = 30,
        budget: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Generate a campaign strategy.
        
        Args:
            brand_id: Brand ID
            campaign_name: Campaign name
            objective: Campaign objective
            duration_days: Campaign duration
            budget: Optional budget
            
        Returns:
            Campaign strategy dictionary
        """
        brand = self.db.query(Brand).filter(Brand.id == brand_id).first()
        if not brand:
            logger.error(f"Brand {brand_id} not found")
            return {}
        
        brand_voice = self.db.query(BrandVoice).filter(
            BrandVoice.brand_id == brand_id
        ).first()
        
        # Use AI to generate campaign strategy
        strategy = await self.ai_analyzer.generate_campaign_strategy(
            brand=brand,
            brand_voice=brand_voice,
            campaign_name=campaign_name,
            objective=objective,
            duration_days=duration_days,
            budget=budget
        )
        
        # Save campaign metrics record
        campaign = CampaignMetrics(
            name=campaign_name,
            start_date=datetime.utcnow(),
            end_date=datetime.utcnow() + timedelta(days=duration_days),
            total_posts=0,
            total_impressions=0,
            total_engagements=0,
            engagement_rate=0.0,
            reach=0,
            conversions=0,
            roi=0.0
        )
        
        self.db.add(campaign)
        self.db.commit()
        
        logger.info(f"Generated campaign strategy: {campaign_name}")
        
        return {
            "campaign_id": campaign.id,
            "name": campaign_name,
            "objective": objective,
            "strategy": strategy
        }

    def track_campaign_progress(
        self,
        campaign_id: int,
        posts_count: int,
        impressions: int,
        engagements: int,
        reach: int,
        conversions: int = 0
    ) -> CampaignMetrics:
        """
        Track campaign progress.
        
        Args:
            campaign_id: Campaign ID
            posts_count: Number of posts
            impressions: Total impressions
            engagements: Total engagements
            reach: Total reach
            conversions: Total conversions
            
        Returns:
            Updated CampaignMetrics object
        """
        campaign = self.db.query(CampaignMetrics).filter(
            CampaignMetrics.id == campaign_id
        ).first()
        
        if not campaign:
            logger.error(f"Campaign {campaign_id} not found")
            raise ValueError(f"Campaign {campaign_id} not found")
        
        campaign.total_posts = posts_count
        campaign.total_impressions = impressions
        campaign.total_engagements = engagements
        campaign.reach = reach
        campaign.conversions = conversions
        
        # Calculate rates
        campaign.engagement_rate = (
            (engagements / impressions * 100) if impressions > 0 else 0.0
        )
        
        # Simple ROI calculation (would need actual revenue data)
        campaign.roi = ((conversions * 10) - campaign.total_posts) / campaign.total_posts if campaign.total_posts > 0 else 0.0
        
        self.db.commit()
        self.db.refresh(campaign)
        
        return campaign
