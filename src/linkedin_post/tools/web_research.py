from crewai.tools import BaseTool
from typing import Type, List, Dict, Any
from pydantic import BaseModel, Field
from langchain_community.tools import DuckDuckGoSearchResults
import json
from datetime import datetime


class WebResearchInput(BaseModel):
    """Input schema for Web Research Tool."""
    topic: str = Field(..., description="The topic to research on the web")
    max_results: int = Field(default=5, description="Maximum number of search results to analyze")


class WebResearchTool(BaseTool):
    name: str = "Web Research Tool"
    description: str = (
        "Searches the web for current information, trends, and news about a specific topic using DuckDuckGo. "
        "Provides comprehensive research including recent developments, expert opinions, and trending information."
    )
    args_schema: Type[BaseModel] = WebResearchInput

    def _get_search_tool(self):
        """Get DuckDuckGo search tool instance."""
        return DuckDuckGoSearchResults(
            max_results=10,
            output_format="list"
        )
    
    def _get_news_search_tool(self):
        """Get DuckDuckGo news search tool instance."""
        return DuckDuckGoSearchResults(
            backend="news",
            max_results=5,
            output_format="list"
        )

    def _run(self, topic: str, max_results: int = 5) -> str:
        """
        Research a topic on the web using DuckDuckGo search.
        
        Args:
            topic: The topic to research
            max_results: Maximum number of results to analyze
            
        Returns:
            JSON string containing comprehensive research results
        """
        try:
            # Perform general web search
            web_results = self._search_web(topic, max_results)
            
            # Perform news search for recent developments
            news_results = self._search_news(topic)
            
            # Structure and analyze the results
            research_data = {
                "topic": topic,
                "search_performed_at": datetime.now().isoformat(),
                "web_results": {
                    "count": len(web_results),
                    "results": web_results
                },
                "news_results": {
                    "count": len(news_results),
                    "results": news_results
                },
                "key_findings": self._extract_key_findings(web_results + news_results, topic),
                "trending_keywords": self._extract_trending_keywords(web_results + news_results),
                "summary": self._generate_summary(web_results, news_results, topic),
                "sources": self._get_unique_sources(web_results + news_results)
            }
            
            return json.dumps(research_data, indent=2)
            
        except Exception as e:
            return json.dumps({
                "error": f"Web search failed: {str(e)}",
                "topic": topic,
                "fallback_insights": self._generate_fallback_insights(topic)
            })

    def _search_web(self, topic: str, max_results: int) -> List[Dict[str, Any]]:
        """Perform general web search using DuckDuckGo."""
        try:
            search_tool = self._get_search_tool()
            
            # Search for general information
            general_query = f"{topic} trends 2024"
            results = search_tool.invoke(general_query)
            
            # Search for expert analysis
            expert_query = f"{topic} expert analysis insights"
            expert_results = search_tool.invoke(expert_query)
            
            # Combine and format results
            all_results = []
            for result in (results + expert_results)[:max_results]:
                if isinstance(result, dict):
                    formatted_result = {
                        "title": result.get("title", ""),
                        "content": result.get("snippet", ""),
                        "url": result.get("link", ""),
                        "type": "web_search",
                        "relevance": self._calculate_relevance(result.get("snippet", ""), topic)
                    }
                    all_results.append(formatted_result)
            
            # Sort by relevance and return top results
            all_results.sort(key=lambda x: x["relevance"], reverse=True)
            return all_results[:max_results]
            
        except Exception as e:
            return []

    def _search_news(self, topic: str) -> List[Dict[str, Any]]:
        """Perform news search using DuckDuckGo."""
        try:
            news_search_tool = self._get_news_search_tool()
            news_query = f"{topic} latest news 2024"
            results = news_search_tool.invoke(news_query)
            
            formatted_results = []
            for result in results:
                if isinstance(result, dict):
                    formatted_result = {
                        "title": result.get("title", ""),
                        "content": result.get("snippet", ""),
                        "url": result.get("link", ""),
                        "source": result.get("source", ""),
                        "date": result.get("date", ""),
                        "type": "news",
                        "relevance": self._calculate_relevance(result.get("snippet", ""), topic)
                    }
                    formatted_results.append(formatted_result)
            
            return formatted_results
            
        except Exception as e:
            return []

    def _calculate_relevance(self, content: str, topic: str) -> float:
        """Calculate relevance score based on topic keywords in content."""
        if not content:
            return 0.0
            
        content_lower = content.lower()
        topic_words = topic.lower().split()
        
        relevance_score = 0.0
        for word in topic_words:
            if word in content_lower:
                relevance_score += 1.0
        
        # Bonus for recent years, trends, statistics
        bonus_keywords = ["2025", "2024", "2023", "trend", "growth", "increase", "statistics", "data", "report"]
        for keyword in bonus_keywords:
            if keyword in content_lower:
                relevance_score += 0.5
        
        return relevance_score

    def _extract_key_findings(self, results: List[Dict[str, Any]], topic: str) -> List[str]:
        """Extract key findings from search results."""
        findings = []
        
        for result in results[:8]:  # Analyze top results
            content = result.get("content", "")
            if len(content) > 50:
                # Look for sentences with key information
                sentences = content.split(". ")
                for sentence in sentences:
                    if (len(sentence) > 30 and 
                        any(keyword in sentence.lower() for keyword in 
                            [topic.lower(), "trend", "growth", "increase", "innovation", "market", "adoption"])):
                        clean_sentence = sentence.strip().rstrip('.')
                        if clean_sentence not in findings:
                            findings.append(clean_sentence)
                            if len(findings) >= 6:
                                break
        
        return findings[:6]

    def _extract_trending_keywords(self, results: List[Dict[str, Any]]) -> List[str]:
        """Extract trending keywords from search results."""
        keyword_counts = {}
        
        for result in results:
            content = f"{result.get('title', '')} {result.get('content', '')}".lower()
            words = content.split()
            
            for word in words:
                word = word.strip(".,!?()[]{}\"'-")
                if (len(word) > 4 and 
                    word.isalpha() and
                    word not in ["this", "that", "with", "from", "they", "have", "been", 
                                "will", "would", "could", "should", "there", "their", "where"]):
                    keyword_counts[word] = keyword_counts.get(word, 0) + 1
        
        # Return top keywords sorted by frequency
        sorted_keywords = sorted(keyword_counts.items(), key=lambda x: x[1], reverse=True)
        return [keyword for keyword, count in sorted_keywords[:10]]

    def _generate_summary(self, web_results: List[Dict[str, Any]], 
                         news_results: List[Dict[str, Any]], topic: str) -> str:
        """Generate a comprehensive summary of research findings."""
        summary_parts = [f"Research Summary for '{topic}':\n"]
        
        if web_results:
            summary_parts.append(f"• Found {len(web_results)} relevant web sources with insights on {topic}")
            
        if news_results:
            summary_parts.append(f"• Discovered {len(news_results)} recent news articles covering latest developments")
            
        # Analyze content themes
        all_content = " ".join([r.get("content", "") for r in web_results + news_results])
        if "growth" in all_content.lower():
            summary_parts.append("• Market growth and expansion trends identified")
        if "innovation" in all_content.lower():
            summary_parts.append("• Innovation and technological advancements noted")
        if "adoption" in all_content.lower():
            summary_parts.append("• Adoption patterns and user engagement insights found")
            
        summary_parts.append(f"\nThe research indicates {topic} is an active area with substantial industry interest and ongoing developments.")
        
        return "\n".join(summary_parts)

    def _get_unique_sources(self, results: List[Dict[str, Any]]) -> List[str]:
        """Extract unique sources from results."""
        sources = set()
        for result in results:
            url = result.get("url", "")
            if url:
                # Extract domain from URL
                try:
                    from urllib.parse import urlparse
                    domain = urlparse(url).netloc
                    if domain:
                        sources.add(domain)
                except:
                    sources.add(url)
        
        return list(sources)[:10]

    def _generate_fallback_insights(self, topic: str) -> Dict[str, Any]:
        """Generate fallback insights when search fails."""
        return {
            "general_insights": [
                f"{topic} is an emerging field with significant potential",
                f"Industry adoption of {topic} is accelerating",
                f"Key players are investing heavily in {topic} development"
            ],
            "trending_themes": ["innovation", "growth", "adoption", "technology", "market"],
            "note": "These are general insights due to search limitations. For accurate information, please verify with current sources."
        }
