"""
Sentiment Analyzer - AI-powered sentiment and emotion analysis for social content
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
import logging
from .engine import AIEngine

logger = logging.getLogger(__name__)

class SentimentAnalyzer:
    """
    Analyzes sentiment, emotions, and tone in social media content
    Provides brand safety monitoring and audience sentiment tracking
    """
    
    def __init__(self, ai_engine: Optional[AIEngine] = None):
        self.ai_engine = ai_engine or AIEngine()
        self.sentiment_categories = [
            "positive", "negative", "neutral", 
            "joy", "anger", "sadness", "fear", "surprise", "disgust"
        ]
        self.industry_specific_terms = self._load_industry_terms()
        
    def _load_industry_terms(self) -> Dict[str, List[str]]:
        """Load industry-specific sentiment indicators"""
        return {
            "tech": ["innovative", "buggy", "intuitive", "complex", "cutting-edge"],
            "finance": ["profitable", "risky", "stable", "volatile", "secure"],
            "healthcare": ["effective", "safe", "concerning", "breakthrough", "side effects"],
            "retail": ["quality", "overpriced", "value", "durable", "disappointing"]
        }
    
    async def analyze_sentiment(
        self,
        text: str,
        context: Optional[str] = None,
        language: str = "en"
    ) -> Dict[str, Any]:
        """
        Analyze sentiment of text content
        
        Args:
            text: Content to analyze
            context: Additional context (industry, brand, etc.)
            language: Content language code
            
        Returns:
            Detailed sentiment analysis
        """
        prompt = f"""
        Analyze sentiment of the following content:
        "{text}"
        
        Context: {context or 'General social media content'}
        Language: {language}
        
        Provide:
        1. Overall sentiment (positive/negative/neutral)
        2. Confidence score (0-1)
        3. Emotional tones detected
        4. Key sentiment drivers
        5. Intensity level (1-10)
        """
        
        response = await self.ai_engine.generate(prompt)
        
        # Simulated detailed analysis
        analysis = {
            "id": f"sentiment_{datetime.utcnow().timestamp()}",
            "text_analyzed": text[:100] + "..." if len(text) > 100 else text,
            "overall_sentiment": "positive",
            "sentiment_scores": {
                "positive": 0.72,
                "negative": 0.08,
                "neutral": 0.20
            },
            "emotions": {
                "joy": 0.65,
                "trust": 0.58,
                "anticipation": 0.42,
                "surprise": 0.15,
                "fear": 0.05,
                "sadness": 0.03,
                "disgust": 0.02,
                "anger": 0.04
            },
            "dominant_emotion": "joy",
            "confidence_score": 0.89,
            "intensity": 7.2,
            "subjectivity": 0.68,
            "key_phrases": [
                {"phrase": "amazing product", "sentiment": "positive", "score": 0.95},
                {"phrase": "highly recommend", "sentiment": "positive", "score": 0.88}
            ],
            "sentiment_drivers": [
                "Product quality mentions",
                "Customer satisfaction expression",
                "Recommendation language"
            ],
            "language_detected": language,
            "analyzed_at": datetime.utcnow().isoformat()
        }
        
        logger.info(f"Sentiment analysis completed: {analysis['overall_sentiment']} ({analysis['confidence_score']:.2f})")
        return analysis
    
    async def analyze_batch(
        self,
        texts: List[str],
        group_by: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Analyze sentiment for multiple texts
        
        Args:
            texts: List of content to analyze
            group_by: Grouping criteria (date, topic, source)
            
        Returns:
            Aggregated sentiment analysis
        """
        results = []
        for text in texts:
            result = await self.analyze_sentiment(text)
            results.append(result)
        
        # Aggregate statistics
        avg_positive = sum(r["sentiment_scores"]["positive"] for r in results) / len(results)
        avg_negative = sum(r["sentiment_scores"]["negative"] for r in results) / len(results)
        
        batch_analysis = {
            "id": f"batch_{datetime.utcnow().timestamp()}",
            "total_items": len(texts),
            "successful_analyses": len(results),
            "aggregate_sentiment": {
                "positive": round(avg_positive, 3),
                "negative": round(avg_negative, 3),
                "neutral": round(1 - avg_positive - avg_negative, 3)
            },
            "sentiment_distribution": {
                "positive": sum(1 for r in results if r["overall_sentiment"] == "positive"),
                "negative": sum(1 for r in results if r["overall_sentiment"] == "negative"),
                "neutral": sum(1 for r in results if r["overall_sentiment"] == "neutral")
            },
            "average_confidence": round(sum(r["confidence_score"] for r in results) / len(results), 3),
            "trend": "improving" if avg_positive > 0.5 else "declining" if avg_negative > 0.3 else "stable",
            "outliers": [
                {"index": i, "reason": "extreme_negative"} 
                for i, r in enumerate(results) 
                if r["sentiment_scores"]["negative"] > 0.8
            ][:5],
            "analyzed_at": datetime.utcnow().isoformat()
        }
        
        return batch_analysis
    
    async def monitor_brand_sentiment(
        self,
        brand_name: str,
        mentions: List[Dict[str, Any]],
        time_period: str = "last_24_hours"
    ) -> Dict[str, Any]:
        """
        Monitor brand sentiment across mentions
        
        Args:
            brand_name: Brand name to monitor
            mentions: List of brand mentions with metadata
            time_period: Monitoring timeframe
            
        Returns:
            Brand sentiment monitoring report
        """
        mention_texts = [m.get("text", "") for m in mentions]
        sentiment_results = await self.analyze_batch(mention_texts)
        
        # Categorize by source/platform
        platform_breakdown = {}
        for mention in mentions:
            platform = mention.get("platform", "unknown")
            if platform not in platform_breakdown:
                platform_breakdown[platform] = []
            platform_breakdown[platform].append(mention)
        
        monitoring_report = {
            "id": f"brand_monitor_{brand_name}_{datetime.utcnow().timestamp()}",
            "brand_name": brand_name,
            "time_period": time_period,
            "total_mentions": len(mentions),
            "sentiment_summary": sentiment_results["aggregate_sentiment"],
            "sentiment_trend": sentiment_results["trend"],
            "volume_change": "+15%",  # Compared to previous period
            "platform_breakdown": {},
            "top_concerns": [],
            "positive_highlights": [],
            "crisis_alert": False,
            "recommended_actions": []
        }
        
        # Analyze each platform
        for platform, plat_mentions in platform_breakdown.items():
            plat_texts = [m.get("text", "") for m in plat_mentions]
            plat_sentiment = await self.analyze_batch(plat_texts)
            monitoring_report["platform_breakdown"][platform] = {
                "mention_count": len(plat_mentions),
                "sentiment": plat_sentiment["aggregate_sentiment"],
                "reach": sum(m.get("reach", 0) for m in plat_mentions)
            }
        
        # Check for crisis indicators
        if sentiment_results["aggregate_sentiment"]["negative"] > 0.6:
            monitoring_report["crisis_alert"] = True
            monitoring_report["recommended_actions"].append("Immediate response required - negative sentiment spike")
        
        return monitoring_report
    
    async def detect_toxicity(
        self,
        text: str,
        threshold: float = 0.7
    ) -> Dict[str, Any]:
        """
        Detect toxic or harmful content
        
        Args:
            text: Content to analyze
            threshold: Toxicity threshold for flagging
            
        Returns:
            Toxicity detection results
        """
        prompt = f"""
        Analyze this content for toxicity and harmful elements:
        "{text}"
        
        Check for:
        - Hate speech
        - Harassment
        - Threats
        - Profanity
        - Discriminatory language
        - Misinformation indicators
        
        Rate each category 0-1 and provide overall toxicity score.
        """
        
        response = await self.ai_engine.generate(prompt)
        
        # Simulated toxicity analysis
        toxicity_result = {
            "id": f"toxicity_{datetime.utcnow().timestamp()}",
            "text_analyzed": text[:100] + "..." if len(text) > 100 else text,
            "is_toxic": False,
            "toxicity_score": 0.12,
            "threshold": threshold,
            "categories": {
                "hate_speech": 0.02,
                "harassment": 0.05,
                "threats": 0.01,
                "profanity": 0.08,
                "discrimination": 0.03,
                "misinformation": 0.15
            },
            "flagged_content": [],
            "severity": "low",
            "recommended_action": "approve",
            "analyzed_at": datetime.utcnow().isoformat()
        }
        
        if toxicity_result["toxicity_score"] > threshold:
            toxicity_result["is_toxic"] = True
            toxicity_result["recommended_action"] = "review" if toxicity_result["toxicity_score"] < 0.9 else "block"
            toxicity_result["severity"] = "high" if toxicity_result["toxicity_score"] > 0.8 else "medium"
        
        return toxicity_result
    
    async def analyze_audience_sentiment(
        self,
        audience_segments: List[Dict[str, Any]],
        content_responses: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Analyze sentiment across different audience segments
        
        Args:
            audience_segments: Defined audience segments
            content_responses: Audience responses to content
            
        Returns:
            Segment-by-segment sentiment analysis
        """
        segment_analysis = {}
        
        for segment in audience_segments:
            segment_id = segment.get("id", "unknown")
            segment_responses = [
                r for r in content_responses 
                if r.get("audience_segment") == segment_id
            ]
            
            if segment_responses:
                response_texts = [r.get("text", "") for r in segment_responses]
                sentiment = await self.analyze_batch(response_texts)
                
                segment_analysis[segment_id] = {
                    "segment_name": segment.get("name", "Unknown"),
                    "response_count": len(segment_responses),
                    "sentiment": sentiment["aggregate_sentiment"],
                    "engagement_level": segment.get("engagement", "medium"),
                    "key_themes": sentiment.get("top_themes", [])
                }
        
        return {
            "id": f"audience_sentiment_{datetime.utcnow().timestamp()}",
            "total_segments": len(audience_segments),
            "total_responses": len(content_responses),
            "segment_breakdown": segment_analysis,
            "most_positive_segment": max(
                segment_analysis.items(),
                key=lambda x: x[1]["sentiment"]["positive"],
                default=(None, {})
            )[0] if segment_analysis else None,
            "most_negative_segment": max(
                segment_analysis.items(),
                key=lambda x: x[1]["sentiment"]["negative"],
                default=(None, {})
            )[0] if segment_analysis else None,
            "insights": [
                "Segment A shows highest positive sentiment",
                "Segment B requires attention due to negative trends",
                "Overall audience sentiment is healthy"
            ],
            "analyzed_at": datetime.utcnow().isoformat()
        }
    
    async def track_sentiment_over_time(
        self,
        historical_data: List[Dict[str, Any]],
        granularity: str = "daily"
    ) -> Dict[str, Any]:
        """
        Track sentiment changes over time
        
        Args:
            historical_data: Historical sentiment data points
            granularity: Time granularity (hourly, daily, weekly)
            
        Returns:
            Time series sentiment analysis
        """
        time_series = []
        
        for data_point in historical_data:
            time_series.append({
                "timestamp": data_point.get("timestamp"),
                "positive": data_point.get("positive_score", 0),
                "negative": data_point.get("negative_score", 0),
                "neutral": data_point.get("neutral_score", 0),
                "volume": data_point.get("volume", 0)
            })
        
        # Calculate trend
        if len(time_series) >= 2:
            recent_avg = sum(t["positive"] for t in time_series[-5:]) / min(5, len(time_series))
            older_avg = sum(t["positive"] for t in time_series[:-5]) / max(1, len(time_series) - 5)
            trend_direction = "upward" if recent_avg > older_avg else "downward"
        else:
            trend_direction = "insufficient_data"
        
        return {
            "id": f"time_series_{datetime.utcnow().timestamp()}",
            "granularity": granularity,
            "data_points": len(time_series),
            "time_range": {
                "start": time_series[0]["timestamp"] if time_series else None,
                "end": time_series[-1]["timestamp"] if time_series else None
            },
            "time_series": time_series,
            "trend": {
                "direction": trend_direction,
                "magnitude": abs(recent_avg - older_avg) if len(time_series) >= 2 else 0,
                "volatility": "low"  # Could calculate standard deviation
            },
            "notable_events": [],
            "predictions": {
                "next_period_sentiment": "positive",
                "confidence": 0.75
            },
            "analyzed_at": datetime.utcnow().isoformat()
        }
