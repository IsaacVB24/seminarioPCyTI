"""LLM-powered article filtering using Groq."""
import os
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv
from groq import AsyncGroq

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

# Create logs directory
LOGS_DIR = Path(__file__).parent.parent.parent / "filter_logs"
LOGS_DIR.mkdir(exist_ok=True)


class LLMArticleFilter:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        if self.api_key:
            self.client = AsyncGroq(api_key=self.api_key)
        else:
            self.client = None
            logger.warning("No GROQ_API_KEY found. LLM filtering will be disabled.")

    async def filter_articles(self, query: str, articles: list[dict], context: Optional[str] = None, max_articles: int = 20) -> list[dict]:
        """
        Filter and rank articles by relevance using LLM.
        
        Args:
            query: User's search query
            articles: List of articles to filter
            context: Additional context/criteria for filtering
            max_articles: Maximum number of articles to send to LLM
            
        Returns:
            Filtered and ranked list of articles with relevance scores
        """
        if not self.client or not articles:
            logger.info("[LLM_FILTER] Skipping - no API key or no articles")
            return articles

        # Limit to prevent excessive token usage
        articles_to_analyze = articles[:max_articles]
        
        logger.info(f"[LLM_FILTER] Analyzing {len(articles_to_analyze)} articles for query: '{query}'")
        if context:
            logger.info(f"[LLM_FILTER] Using context: '{context}'")

        # Build prompt with article data
        articles_text = self._format_articles_for_prompt(articles_to_analyze)
        
        # Build context instruction
        context_instruction = ""
        if context and context.strip():
            context_instruction = f"\n\nAdditional Context: The user is specifically looking for: {context.strip()}\nConsider this context when evaluating relevance."
        
        prompt = f"""You are a scientific article relevance evaluator.

User Query: "{query}"{context_instruction}

Articles to evaluate:
{articles_text}

Task: Analyze each article and determine its relevance to the user's query{' and the provided context' if context else ''}.
For each article, assign a relevance score from 0.0 to 1.0 where:
- 1.0 = Highly relevant, directly addresses the query{' and context' if context else ''}
- 0.7-0.9 = Very relevant, closely related
- 0.5-0.6 = Moderately relevant, tangentially related
- Below 0.5 = Not very relevant

Return ONLY a JSON array with this exact format:
[
  {{"index": 0, "score": 0.95, "reason": "Brief explanation"}},
  {{"index": 1, "score": 0.75, "reason": "Brief explanation"}}
]

Only include articles with score >= 0.5. Order by score (highest first)."""

        try:
            response = await self.client.chat.completions.create(
                model="llama-3.3-70b-versatile",  # Updated to current model
                messages=[
                    {"role": "system", "content": "You are a scientific research assistant that evaluates article relevance."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,  # Lower temperature for more consistent scoring
                max_tokens=2000,
            )
            
            result_text = response.choices[0].message.content.strip()
            logger.debug(f"[LLM_FILTER] Raw response: {result_text}")
            
            # Parse JSON response
            import json
            # Extract JSON from markdown code blocks if present
            if "```json" in result_text:
                result_text = result_text.split("```json")[1].split("```")[0].strip()
            elif "```" in result_text:
                result_text = result_text.split("```")[1].split("```")[0].strip()
            
            rankings = json.loads(result_text)
            
            # Build filtered results
            filtered_articles = []
            for rank in rankings:
                idx = rank["index"]
                if 0 <= idx < len(articles_to_analyze):
                    article = articles_to_analyze[idx].copy()
                    article["llm_relevance_score"] = rank["score"]
                    article["llm_relevance_reason"] = rank.get("reason", "")
                    filtered_articles.append(article)
            
            logger.info(f"[LLM_FILTER] Filtered to {len(filtered_articles)} relevant articles")
            
        except Exception as e:
            logger.error(f"[LLM_FILTER] Error: {e}")
            # Fallback to original articles on error
            filtered_articles = articles
        
        # Save before/after comparison (always, even on error)
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            self._save_articles_to_markdown(articles_to_analyze, f"before_filter_{timestamp}.md", query, context)
            self._save_articles_to_markdown(filtered_articles, f"after_filter_{timestamp}.md", query, context)
            logger.info(f"[LLM_FILTER] Saved comparison to filter_logs/{timestamp}")
        except Exception as save_error:
            logger.error(f"[LLM_FILTER] Failed to save files: {save_error}")
        
        return filtered_articles

    def _format_articles_for_prompt(self, articles: list[dict]) -> str:
        """Format articles for LLM prompt."""
        lines = []
        for i, article in enumerate(articles):
            title = article.get("title", "No title")
            authors = article.get("authors", [])
            author_names = ", ".join([a.get("name", "") for a in authors[:3]])
            if len(authors) > 3:
                author_names += " et al."
            snippet = article.get("snippet", "")[:200]  # Limit snippet length
            
            lines.append(f"{i}. Title: {title}")
            lines.append(f"   Authors: {author_names}")
            lines.append(f"   Abstract: {snippet}")
            lines.append("")
        
        return "\n".join(lines)

    def _save_articles_to_markdown(self, articles: list[dict], filename: str, query: str, context: Optional[str] = None):
        """Save articles to a markdown file."""
        try:
            filepath = LOGS_DIR / filename
            
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(f"# Article Filter Log\n\n")
                f.write(f"**Query:** {query}\n\n")
                if context:
                    f.write(f"**Context:** {context}\n\n")
                f.write(f"**Timestamp:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                f.write(f"**Total Articles:** {len(articles)}\n\n")
                f.write("---\n\n")
                
                for i, article in enumerate(articles, 1):
                    f.write(f"## {i}. {article.get('title', 'No title')}\n\n")
                    
                    # Source badge
                    source = article.get('source', 'unknown')
                    f.write(f"**Source:** {source.upper()}\n\n")
                    
                    # LLM scores if available
                    if "llm_relevance_score" in article:
                        f.write(f"**🤖 Relevance Score:** {article['llm_relevance_score']:.2f}\n\n")
                        if article.get("llm_relevance_reason"):
                            f.write(f"**Reason:** {article['llm_relevance_reason']}\n\n")
                    
                    # Authors
                    authors = article.get('authors', [])
                    if authors:
                        author_names = ", ".join([a.get("name", "") for a in authors[:5]])
                        if len(authors) > 5:
                            author_names += f" et al. ({len(authors)} authors)"
                        f.write(f"**Authors:** {author_names}\n\n")
                    
                    # Publication info
                    journal = article.get('journal', '')
                    pub_date = article.get('pub_date', '')
                    if journal or pub_date:
                        f.write(f"**Published:** {journal} ({pub_date})\n\n")
                    
                    # Links
                    url = article.get('url', '')
                    pdf_url = article.get('pdf_url', '')
                    doi = article.get('doi', '')
                    
                    links = []
                    if url:
                        links.append(f"[Article]({url})")
                    if pdf_url:
                        links.append(f"[PDF]({pdf_url})")
                    if doi:
                        links.append(f"[DOI](https://doi.org/{doi})")
                    
                    if links:
                        f.write(" | ".join(links) + "\n\n")
                    
                    # Abstract/snippet
                    snippet = article.get('snippet', '')
                    if snippet:
                        f.write(f"**Abstract:**\n\n{snippet}\n\n")
                    
                    f.write("---\n\n")
            
            logger.info(f"[LLM_FILTER] Saved {len(articles)} articles to {filepath}")
        except Exception as e:
            logger.error(f"[LLM_FILTER] Failed to save markdown: {e}")


# Global instance
_filter = LLMArticleFilter()


async def filter_articles_with_llm(query: str, articles: list[dict], context: Optional[str] = None) -> list[dict]:
    """Convenience function to filter articles."""
    return await _filter.filter_articles(query, articles, context)
