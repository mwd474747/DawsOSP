"""
DawsOS Claude Agent

Purpose: AI-powered explanations and analysis
Updated: 2025-11-02

Capabilities:
    - claude.explain: Generate explanations for metrics, ratings, decisions
    - claude.summarize: Summarize portfolio changes, news, reports
    - claude.analyze: Analyze patterns in data
    - claude.portfolio_advice: Provide personalized portfolio advice
    - claude.financial_qa: Answer general financial questions
    - claude.scenario_analysis: Analyze what-if scenarios
    - ai.explain: Alternative capability name for explanations

Architecture:
    Pattern → Agent Runtime → ClaudeAgent → Anthropic Claude API (claude-3-sonnet)

Usage:
    agent = ClaudeAgent("claude_agent", services)
    runtime.register_agent(agent)
"""

import logging
import os
import json
import httpx
from typing import Any, Dict, List, Optional

from app.agents.base_agent import BaseAgent
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
        
        # Check for Replit managed credentials first, then fall back to user's key
        self.api_key = os.environ.get("AI_INTEGRATIONS_ANTHROPIC_API_KEY") or os.environ.get("ANTHROPIC_API_KEY")
        
        # Use Replit's base URL if available, otherwise use default
        self.api_url = os.environ.get("AI_INTEGRATIONS_ANTHROPIC_BASE_URL") or "https://api.anthropic.com/v1/messages"
        
        # Use updated Claude model
        self.model = "claude-3-5-sonnet-20241022"  # Updated to latest Sonnet model
        
        # Track which integration method is being used
        self.using_replit_integration = bool(os.environ.get("AI_INTEGRATIONS_ANTHROPIC_API_KEY"))
        
        if self.using_replit_integration:
            logger.info("Using Replit managed Anthropic integration")
        elif self.api_key:
            logger.info("Using user-provided ANTHROPIC_API_KEY")
        else:
            logger.warning("No Anthropic API credentials found")
        
    async def _call_claude(self, system_prompt: str, user_prompt: str, temperature: float = 0.7) -> str:
        """Call Claude API with error handling."""
        if not self.api_key:
            return "Claude API key not configured. Please set up the Replit Anthropic integration or provide your own ANTHROPIC_API_KEY environment variable."
            
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

        # Prepare context information for Claude
        context_str = ""
        value = None
        
        if context:
            value = context.get(subject)
            # Build context string with relevant financial data
            context_str = f"Context Information:\n"
            for key, val in context.items():
                if val is not None:
                    if isinstance(val, (int, float)):
                        context_str += f"- {key}: {val:.4f}\n"
                    elif isinstance(val, dict):
                        context_str += f"- {key}: {json.dumps(val, default=str, indent=2)}\n"
                    else:
                        context_str += f"- {key}: {str(val)}\n"
        
        # Add state information if available
        if state:
            if "positions" in state:
                positions = state.get("positions", [])
                if positions:
                    context_str += f"\nPortfolio has {len(positions)} positions\n"
                    # Add top holdings for context
                    if "valued_positions" in state:
                        valued = state["valued_positions"]
                        if isinstance(valued, list):
                            sorted_positions = sorted(valued, key=lambda x: x.get("value", 0), reverse=True)[:5]
                            context_str += "Top Holdings:\n"
                            for pos in sorted_positions:
                                context_str += f"- {pos.get('symbol', 'N/A')}: ${pos.get('value', 0):,.2f}\n"
                    
            if "perf_metrics" in state:
                metrics = state.get("perf_metrics", {})
                context_str += f"\nPerformance Metrics:\n"
                for key, val in metrics.items():
                    if isinstance(val, (int, float)):
                        context_str += f"- {key}: {val:.4f}\n"
        
        # Create system prompt for financial explanation
        system_prompt = """You are a senior financial advisor providing clear, data-driven explanations of portfolio metrics and financial concepts.
        Break down complex financial metrics into understandable components.
        Provide specific reasoning based on the actual data provided.
        Be quantitative and precise when discussing financial values.
        Format your response as JSON with these exact fields:
        {
            "explanation": "A clear, one-paragraph explanation of the metric",
            "reasoning": ["First specific insight", "Second specific insight", "Third specific insight"],
            "confidence": "high/medium/low based on data completeness"
        }"""
        
        # Create user prompt
        user_prompt = f"""Explain this financial metric or concept: {subject}
        
{context_str}

Current Value: {value if value is not None else 'Not provided'}

Provide a detailed explanation with 3-5 specific reasoning points based on the portfolio data provided. Be specific about how the portfolio holdings and metrics contribute to this value."""

        # Call Claude API
        response_text = await self._call_claude(system_prompt, user_prompt, temperature=0.3)
        
        # Parse response or use as-is
        try:
            # Try to parse as JSON if Claude returns structured response
            if response_text.startswith("{"):
                response_data = json.loads(response_text)
                explanation = response_data.get("explanation", response_text)
                reasoning = response_data.get("reasoning", [])
                confidence = response_data.get("confidence", "medium")
            else:
                # If not JSON, extract insights from text
                explanation = response_text
                # Split into sentences and take meaningful insights
                sentences = [s.strip() for s in response_text.split(".") if s.strip() and len(s.strip()) > 20]
                reasoning = sentences[1:4] if len(sentences) > 1 else ["Based on portfolio analysis"]
                confidence = "medium"
        except (json.JSONDecodeError, Exception) as e:
            logger.debug(f"Could not parse JSON response: {e}")
            explanation = response_text
            reasoning = ["Analysis based on portfolio data provided"]
            confidence = "medium"
        
        result = {
            "subject": subject,
            "value": value,
            "explanation": explanation,
            "reasoning": reasoning if isinstance(reasoning, list) else [reasoning],
            "confidence": confidence,
        }

        # Attach metadata
        metadata = self._create_metadata(
            source="claude_api:explain",
            asof=ctx.asof_date,
            ttl=self.CACHE_TTL_HOUR,  # Cache for 1 hour
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

        # Prepare content type-specific prompts
        content_type_prompts = {
            "news": "financial news article",
            "report": "financial report",
            "portfolio": "portfolio performance summary",
            "text": "document"
        }
        
        content_description = content_type_prompts.get(content_type, "content")
        
        # Create system prompt for summarization
        system_prompt = f"""You are a financial analyst creating concise summaries of {content_description}s.
        Create clear, informative summaries that capture the most important information.
        Focus on financial impacts, key metrics, and actionable insights.
        Format your response as JSON with these exact fields:
        {{
            "summary": "A concise summary in {max_length} words or less",
            "key_points": ["First key point", "Second key point", "Third key point"],
            "financial_impact": "Brief description of financial implications if applicable"
        }}"""
        
        # Truncate content if too long for API
        max_content_chars = 10000
        truncated_content = content[:max_content_chars] if len(content) > max_content_chars else content
        if len(content) > max_content_chars:
            truncated_content += f"\n\n[Content truncated - showing first {max_content_chars} characters of {len(content)} total]"
        
        # Add portfolio context if available in state
        portfolio_context = ""
        if state and "positions" in state:
            portfolio_context = "\n\nPortfolio Context: "
            portfolio_context += f"{len(state.get('positions', []))} positions in portfolio"
            if "valued_positions" in state:
                total_value = sum(p.get("value", 0) for p in state.get("valued_positions", []))
                portfolio_context += f", Total Value: ${total_value:,.2f}"
        
        # Create user prompt
        user_prompt = f"""Please summarize the following {content_description} in {max_length} words or less:

{truncated_content}
{portfolio_context}

Focus on the most important information, financial impacts, and actionable insights. Extract 3-5 key points."""

        # Call Claude API
        response_text = await self._call_claude(system_prompt, user_prompt, temperature=0.4)
        
        # Parse response
        try:
            if response_text.startswith("{"):
                response_data = json.loads(response_text)
                summary = response_data.get("summary", response_text)
                key_points = response_data.get("key_points", [])
                financial_impact = response_data.get("financial_impact", "")
            else:
                # Fallback to text parsing
                summary = response_text[:max_length * 10]  # Approximate word to char ratio
                # Extract bullet points or sentences as key points
                lines = response_text.split("\n")
                key_points = [l.strip("- •·").strip() for l in lines if l.strip().startswith(("-", "•", "·"))][:5]
                if not key_points:
                    sentences = [s.strip() for s in response_text.split(".") if s.strip() and len(s.strip()) > 20]
                    key_points = sentences[:3]
                financial_impact = ""
        except (json.JSONDecodeError, Exception) as e:
            logger.debug(f"Could not parse JSON response: {e}")
            summary = response_text[:max_length * 10]
            key_points = ["Summary generated from content analysis"]
            financial_impact = ""
        
        # Count actual words in summary
        summary_words = len(summary.split())
        
        result = {
            "content_type": content_type,
            "original_length": len(content),
            "summary": summary,
            "summary_length": summary_words,
            "key_points": key_points if isinstance(key_points, list) else [key_points],
        }
        
        if financial_impact:
            result["financial_impact"] = financial_impact

        # Attach metadata
        metadata = self._create_metadata(
            source="claude_api:summarize",
            asof=ctx.asof_date,
            ttl=self.CACHE_TTL_HOUR,
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

        # Prepare data for analysis
        data_summary = ""
        data_points = 0
        
        if isinstance(data, list):
            data_points = len(data)
            if data_points > 0:
                # Sample data for context
                sample_size = min(10, data_points)
                data_summary = f"Data contains {data_points} items.\nSample data:\n"
                for item in data[:sample_size]:
                    if isinstance(item, dict):
                        data_summary += f"- {json.dumps(item, default=str, indent=2)[:500]}\n"
                    else:
                        data_summary += f"- {str(item)[:100]}\n"
        elif isinstance(data, dict):
            data_points = len(data)
            data_summary = f"Data contains {data_points} fields:\n"
            for key, val in list(data.items())[:10]:
                if isinstance(val, (list, dict)):
                    data_summary += f"- {key}: {type(val).__name__} with {len(val)} items\n"
                else:
                    data_summary += f"- {key}: {str(val)[:100]}\n"
        else:
            data_points = 1
            data_summary = f"Data type: {type(data).__name__}\nValue: {str(data)[:1000]}"
        
        # Add portfolio context from state
        portfolio_context = ""
        if state:
            if "positions" in state:
                portfolio_context += f"\nPortfolio Context: {len(state.get('positions', []))} positions"
            if "perf_metrics" in state:
                metrics = state.get("perf_metrics", {})
                if metrics:
                    portfolio_context += f"\nKey Metrics:"
                    for key in ["twr_ytd", "sharpe_ratio", "volatility", "max_drawdown"]:
                        if key in metrics:
                            portfolio_context += f"\n- {key}: {metrics[key]:.4f}"
            if "historical_nav" in state:
                nav_data = state.get("historical_nav", {})
                if "values" in nav_data:
                    portfolio_context += f"\nHistorical Data: {len(nav_data['values'])} data points"
        
        # Analysis type specific prompts
        analysis_prompts = {
            "general": "Provide general insights and patterns",
            "anomaly": "Identify any unusual patterns, outliers, or anomalies",
            "trend": "Analyze trends, momentum, and directional changes",
            "risk": "Assess risk factors and potential vulnerabilities",
            "opportunity": "Identify opportunities for improvement or optimization"
        }
        
        analysis_focus = analysis_prompts.get(analysis_type, analysis_prompts["general"])
        
        # Create system prompt
        system_prompt = f"""You are a quantitative financial analyst specializing in data analysis and pattern recognition.
        Analyze the provided financial data to {analysis_focus}.
        Be specific and quantitative in your insights.
        Format your response as JSON with these exact fields:
        {{
            "insights": ["First key insight", "Second key insight", "Third key insight"],
            "patterns_detected": "Brief description of patterns found",
            "recommendations": ["First recommendation", "Second recommendation"],
            "confidence": "high/medium/low based on data quality and completeness",
            "risk_factors": "Any identified risks or concerns"
        }}"""
        
        # Create user prompt
        user_prompt = f"""Analyze this financial data for {analysis_type} analysis:

{data_summary}
{portfolio_context}

Data Points: {data_points}
Analysis Type: {analysis_type}

Focus: {analysis_focus}

Provide 3-5 specific insights and 2-3 actionable recommendations based on the data patterns."""

        # Call Claude API
        response_text = await self._call_claude(system_prompt, user_prompt, temperature=0.4)
        
        # Parse response
        try:
            if response_text.startswith("{"):
                response_data = json.loads(response_text)
                insights = response_data.get("insights", [])
                patterns = response_data.get("patterns_detected", "")
                recommendations = response_data.get("recommendations", [])
                confidence = response_data.get("confidence", "medium")
                risk_factors = response_data.get("risk_factors", "")
            else:
                # Fallback parsing
                lines = response_text.split("\n")
                insights = [l.strip("- •·").strip() for l in lines if l.strip() and len(l.strip()) > 20][:5]
                if not insights:
                    insights = ["Analysis completed based on available data"]
                recommendations = []
                patterns = ""
                confidence = "medium"
                risk_factors = ""
        except (json.JSONDecodeError, Exception) as e:
            logger.debug(f"Could not parse JSON response: {e}")
            insights = [response_text[:200] if response_text else "Analysis based on provided data"]
            recommendations = []
            patterns = ""
            confidence = "medium" 
            risk_factors = ""
        
        result = {
            "analysis_type": analysis_type,
            "data_points": data_points,
            "insights": insights if isinstance(insights, list) else [insights],
            "confidence": confidence,
            "recommendations": recommendations if isinstance(recommendations, list) else [],
        }
        
        if patterns:
            result["patterns_detected"] = patterns
        if risk_factors:
            result["risk_factors"] = risk_factors

        # Attach metadata
        metadata = self._create_metadata(
            source="claude_api:analyze",
            asof=ctx.asof_date,
            ttl=self.CACHE_TTL_HOUR,
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
            ttl=self.CACHE_TTL_30MIN,  # Cache for 30 minutes
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
            ttl=self.CACHE_TTL_HOUR,  # Cache for 1 hour
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
            ttl=self.CACHE_TTL_30MIN,  # Cache for 30 minutes
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
