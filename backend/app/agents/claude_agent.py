"""
DawsOS Claude Agent

Purpose: AI-powered explanations and analysis
Created: 2025-10-23 (P0 fix from CODEBASE_AUDIT_REPORT.md)
Priority: P1 (Important for user experience)

Capabilities:
    - claude.explain: Generate explanations for metrics, ratings, decisions
    - claude.summarize: Summarize portfolio changes, news, reports
    - claude.analyze: Analyze patterns in data
    - claude.portfolio_advice: Provide personalized portfolio advice
    - claude.financial_qa: Answer general financial questions
    - claude.scenario_analysis: Analyze what-if scenarios

Architecture:
    Pattern → Agent Runtime → ClaudeAgent → Anthropic API

Usage:
    agent = ClaudeAgent("claude", services)
    runtime.register_agent(agent)
"""

import logging
import os
import json
import httpx
from typing import Any, Dict, List, Optional

from app.agents.base_agent import BaseAgent, AgentMetadata
from app.core.types import RequestCtx

logger = logging.getLogger("DawsOS.ClaudeAgent")


class ClaudeAgent(BaseAgent):
    """
    Claude AI Agent.

    Provides capabilities for:
        - Explaining metrics, ratings, and decisions
        - Summarizing portfolio changes and news
        - Analyzing patterns in data
        - Providing portfolio advice
        - Answering financial questions
        - Analyzing what-if scenarios

    Integrates with:
        - Anthropic Claude API (for AI explanations)
        - RequestCtx (for trace-aware context)

    Features:
        - Trace-aware explanations (uses execution trace)
        - Context-aware responses
        - Caching for efficiency
    """
    
    def __init__(self, agent_id: str, services: Dict[str, Any] = None):
        super().__init__(agent_id, services)
        self.api_key = os.environ.get("ANTHROPIC_API_KEY")
        self.api_url = "https://api.anthropic.com/v1/messages"
        self.model = "claude-3-sonnet-20240229"  # Using Sonnet for balance of cost and performance
        
    async def _call_claude(self, system_prompt: str, user_prompt: str, temperature: float = 0.7) -> str:
        """Call Claude API with error handling."""
        if not self.api_key:
            return "Claude API key not configured. Please set ANTHROPIC_API_KEY environment variable."
            
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "max_tokens": 1000,
            "temperature": temperature,
            "system": system_prompt,
            "messages": [
                {"role": "user", "content": user_prompt}
            ]
        }
        
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.post(self.api_url, json=payload, headers=headers)
                
                if response.status_code == 200:
                    data = response.json()
                    return data["content"][0]["text"]
                else:
                    logger.error(f"Claude API error: {response.status_code} - {response.text}")
                    return f"API error: {response.status_code}. Using fallback response."
        except Exception as e:
            logger.error(f"Claude API call failed: {e}")
            return "Unable to connect to Claude AI. Please check your connection."

    def get_capabilities(self) -> List[str]:
        """Return list of capabilities."""
        return [
            "claude.explain",
            "claude.summarize",
            "claude.analyze",
            "ai.explain",  # Alias for claude.explain for pattern compatibility
            "claude.portfolio_advice",
            "claude.financial_qa",
            "claude.scenario_analysis"
        ]

    async def claude_explain(
        self,
        ctx: RequestCtx,
        state: Dict[str, Any],
        subject: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Generate explanation for a metric, rating, or decision.

        Uses AI to explain why a particular value or decision was made,
        using the execution trace and context for transparency.

        Args:
            ctx: Request context (includes trace)
            state: Execution state
            subject: What to explain (e.g., "twr_ytd", "sharpe_ratio", "regime")
            context: Additional context (optional)

        Returns:
            Dict with explanation

        Example:
            {
                "subject": "twr_ytd",
                "value": 0.0850,
                "explanation": "Your portfolio's year-to-date return of 8.5% is driven by...",
                "reasoning": [
                    "Strong performance in technology holdings (+12.5%)",
                    "Offset by weaker financial sector (-2.3%)",
                    "Currency headwinds reduced returns by -0.8%"
                ],
                "confidence": "high",
                "__metadata__": {...}
            }
        """
        logger.info(f"claude.explain: subject={subject}")

        # TODO: Implement Claude API integration
        # For now, return placeholder explanation
        result = {
            "subject": subject,
            "value": context.get(subject) if context else None,
            "explanation": f"[AI Explanation for {subject} would appear here]",
            "reasoning": [
                "Placeholder reasoning point 1",
                "Placeholder reasoning point 2",
                "Placeholder reasoning point 3",
            ],
            "confidence": "medium",
            "note": "Claude API integration not yet implemented",
        }

        # Attach metadata
        metadata = self._create_metadata(
            source="claude_api:explain",
            asof=ctx.asof_date,
            ttl=3600,  # Cache for 1 hour
        )
        result = self._attach_metadata(result, metadata)

        return result

    async def claude_summarize(
        self,
        ctx: RequestCtx,
        state: Dict[str, Any],
        content: str,
        content_type: str = "text",
        max_length: int = 200,
    ) -> Dict[str, Any]:
        """
        Summarize content (portfolio changes, news, reports).

        Uses AI to generate concise summaries of longer content.

        Args:
            ctx: Request context
            state: Execution state
            content: Content to summarize
            content_type: Type of content ("text", "news", "report")
            max_length: Maximum summary length in words

        Returns:
            Dict with summary

        Example:
            {
                "content_type": "news",
                "original_length": 5000,
                "summary": "Apple announced new products including...",
                "summary_length": 150,
                "key_points": [
                    "New product launch announced",
                    "Revenue guidance increased",
                    "Stock price up 3%"
                ],
                "__metadata__": {...}
            }
        """
        logger.info(
            f"claude.summarize: content_type={content_type}, "
            f"content_length={len(content)}, max_length={max_length}"
        )

        # TODO: Implement Claude API integration
        result = {
            "content_type": content_type,
            "original_length": len(content),
            "summary": "[AI Summary would appear here]",
            "summary_length": 0,
            "key_points": [
                "Placeholder key point 1",
                "Placeholder key point 2",
            ],
            "note": "Claude API integration not yet implemented",
        }

        # Attach metadata
        metadata = self._create_metadata(
            source="claude_api:summarize",
            asof=ctx.asof_date,
            ttl=3600,
        )
        result = self._attach_metadata(result, metadata)

        return result

    async def claude_analyze(
        self,
        ctx: RequestCtx,
        state: Dict[str, Any],
        data: Any,
        analysis_type: str = "general",
    ) -> Dict[str, Any]:
        """
        Analyze patterns in data.

        Uses AI to identify patterns, anomalies, and insights in data.

        Args:
            ctx: Request context
            state: Execution state
            data: Data to analyze
            analysis_type: Type of analysis ("general", "anomaly", "trend")

        Returns:
            Dict with analysis

        Example:
            {
                "analysis_type": "trend",
                "data_points": 252,
                "insights": [
                    "Upward trend detected since Q2",
                    "Volatility increasing in recent weeks",
                    "Pattern similar to pre-correction behavior"
                ],
                "confidence": "medium",
                "recommendations": [
                    "Consider increasing cash position",
                    "Review portfolio risk allocation"
                ],
                "__metadata__": {...}
            }
        """
        logger.info(f"claude.analyze: analysis_type={analysis_type}")

        # TODO: Implement Claude API integration
        result = {
            "analysis_type": analysis_type,
            "data_points": len(data) if isinstance(data, (list, dict)) else 0,
            "insights": [
                "Placeholder insight 1",
                "Placeholder insight 2",
            ],
            "confidence": "medium",
            "recommendations": [],
            "note": "Claude API integration not yet implemented",
        }

        # Attach metadata
        metadata = self._create_metadata(
            source="claude_api:analyze",
            asof=ctx.asof_date,
            ttl=3600,
        )
        result = self._attach_metadata(result, metadata)

        return result
    
    async def claude_portfolio_advice(
        self,
        ctx: RequestCtx,
        state: Dict[str, Any],
        question: str,
        portfolio_context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Provide personalized portfolio advice based on current holdings and market conditions.
        
        Args:
            ctx: Request context
            state: Execution state
            question: User's question about their portfolio
            portfolio_context: Portfolio data (positions, metrics, etc.)
            
        Returns:
            Dict with advice
        """
        logger.info(f"claude.portfolio_advice: {question[:100]}...")
        
        # Prepare portfolio summary for context
        portfolio_summary = "Portfolio Context:\n"
        if portfolio_context:
            if "total_value" in portfolio_context:
                portfolio_summary += f"- Total Value: ${portfolio_context['total_value']:,.2f}\n"
            if "positions" in portfolio_context:
                portfolio_summary += f"- Number of Positions: {len(portfolio_context['positions'])}\n"
                # Add top 3 positions
                top_positions = sorted(portfolio_context.get('positions', []), 
                                     key=lambda x: x.get('value', 0), reverse=True)[:3]
                if top_positions:
                    portfolio_summary += "- Top Holdings:\n"
                    for pos in top_positions:
                        weight = (pos.get('value', 0) / portfolio_context.get('total_value', 1)) * 100
                        portfolio_summary += f"  - {pos.get('symbol', 'N/A')}: {weight:.1f}%\n"
        
        system_prompt = """You are a professional financial advisor with expertise in portfolio management. 
        Provide clear, actionable advice based on the user's portfolio and question. 
        Be specific but concise. Consider risk management, diversification, and the user's implied goals."""
        
        user_prompt = f"{portfolio_summary}\n\nUser Question: {question}"
        
        # Call Claude API
        response = await self._call_claude(system_prompt, user_prompt, temperature=0.5)
        
        result = {
            "question": question,
            "advice": response,
            "category": "portfolio_advice",
            "timestamp": ctx.asof_date.isoformat() if ctx.asof_date else None
        }
        
        # Attach metadata
        metadata = self._create_metadata(
            source="claude_api:portfolio_advice",
            asof=ctx.asof_date,
            ttl=1800,  # Cache for 30 minutes
        )
        result = self._attach_metadata(result, metadata)
        
        return result
    
    async def claude_financial_qa(
        self,
        ctx: RequestCtx,
        state: Dict[str, Any],
        question: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Answer general financial questions using Claude's knowledge.
        
        Args:
            ctx: Request context
            state: Execution state
            question: Financial question
            context: Additional context
            
        Returns:
            Dict with answer
        """
        logger.info(f"claude.financial_qa: {question[:100]}...")
        
        system_prompt = """You are a knowledgeable financial expert. 
        Answer financial questions clearly and accurately. 
        Provide educational insights while being practical and actionable.
        If discussing specific investment advice, remind users to consult with their financial advisor."""
        
        user_prompt = f"Question: {question}"
        if context:
            user_prompt += f"\n\nAdditional Context: {json.dumps(context, indent=2)}"
        
        # Call Claude API
        response = await self._call_claude(system_prompt, user_prompt, temperature=0.6)
        
        result = {
            "question": question,
            "answer": response,
            "category": "financial_qa",
            "timestamp": ctx.asof_date.isoformat() if ctx.asof_date else None
        }
        
        # Attach metadata
        metadata = self._create_metadata(
            source="claude_api:financial_qa",
            asof=ctx.asof_date,
            ttl=3600,  # Cache for 1 hour
        )
        result = self._attach_metadata(result, metadata)
        
        return result
    
    async def claude_scenario_analysis(
        self,
        ctx: RequestCtx,
        state: Dict[str, Any],
        scenario: str,
        portfolio_data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Analyze what-if scenarios for the portfolio.
        
        Args:
            ctx: Request context
            state: Execution state
            scenario: What-if scenario description
            portfolio_data: Current portfolio data
            
        Returns:
            Dict with scenario analysis
        """
        logger.info(f"claude.scenario_analysis: {scenario[:100]}...")
        
        # Prepare portfolio context
        portfolio_context = ""
        if portfolio_data:
            portfolio_context = "Current Portfolio:\n"
            if "positions" in portfolio_data:
                for pos in portfolio_data.get("positions", [])[:5]:  # Top 5 positions
                    portfolio_context += f"- {pos.get('symbol', 'N/A')}: ${pos.get('value', 0):,.2f}\n"
        
        system_prompt = """You are a risk management expert specializing in scenario analysis. 
        Analyze the potential impact of hypothetical scenarios on investment portfolios. 
        Provide specific insights about risks, opportunities, and recommended actions.
        Be quantitative where possible but explain impacts clearly."""
        
        user_prompt = f"{portfolio_context}\n\nScenario: {scenario}\n\nAnalyze the potential impact and provide recommendations."
        
        # Call Claude API
        response = await self._call_claude(system_prompt, user_prompt, temperature=0.5)
        
        result = {
            "scenario": scenario,
            "analysis": response,
            "category": "scenario_analysis",
            "timestamp": ctx.asof_date.isoformat() if ctx.asof_date else None
        }
        
        # Attach metadata
        metadata = self._create_metadata(
            source="claude_api:scenario_analysis",
            asof=ctx.asof_date,
            ttl=1800,  # Cache for 30 minutes
        )
        result = self._attach_metadata(result, metadata)
        
        return result

    async def ai_explain(
        self,
        ctx: RequestCtx,
        state: Dict[str, Any],
        topic: str,
        data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Alias for claude.explain for pattern compatibility.

        Capability: ai.explain
        """
        return await self.claude_explain(ctx, state, topic, data)


# ============================================================================
# Factory Function (Singleton Pattern)
# ============================================================================

_claude_agent_instance = None


def get_claude_agent(services: Optional[Dict[str, Any]] = None) -> ClaudeAgent:
    """
    Get or create singleton ClaudeAgent.

    Args:
        services: Services dict (optional)

    Returns:
        ClaudeAgent instance
    """
    global _claude_agent_instance
    if _claude_agent_instance is None:
        _claude_agent_instance = ClaudeAgent("claude", services or {})
        logger.info("ClaudeAgent initialized")
    return _claude_agent_instance
