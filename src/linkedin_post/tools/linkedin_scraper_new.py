from crewai.tools import BaseTool
from typing import Type, List, Dict, Any
from pydantic import BaseModel, Field
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time
import json
import os
import re
from bs4 import BeautifulSoup


class LinkedInScraperInput(BaseModel):
    """Input schema for LinkedIn Scraper."""
    topic: str = Field(..., description="The topic to search for on LinkedIn")
    max_posts: int = Field(default=10, description="Maximum number of posts to scrape")


class LinkedInScraperTool(BaseTool):
    name: str = "LinkedIn Post Scraper"
    description: str = (
        "Scrapes LinkedIn posts related to a specific topic. "
        "Returns post content, engagement metrics, and author information. "
        "Note: This tool requires LinkedIn login credentials to be set as environment variables."
    )
    args_schema: Type[BaseModel] = LinkedInScraperInput

    def _run(self, topic: str, max_posts: int = 10) -> str:
        """
        Scrape LinkedIn posts for a given topic.
        
        Args:
            topic: The topic to search for
            max_posts: Maximum number of posts to scrape
            
        Returns:
            JSON string containing scraped posts data
        """
        try:
            # Check for LinkedIn credentials
            linkedin_email = os.getenv('LINKEDIN_EMAIL')
            linkedin_password = os.getenv('LINKEDIN_PASSWORD')
            
            if not linkedin_email or not linkedin_password:
                return json.dumps({
                    "error": "LinkedIn credentials not found",
                    "message": "Please add LINKEDIN_EMAIL and LINKEDIN_PASSWORD to your .env file to access real LinkedIn posts",
                    "fallback": "Using mock data for development",
                    "mock_data": self._generate_mock_linkedin_data(topic, max_posts)
                })
            
            # Use simple Chrome setup like the working example
            try:
                service = Service(ChromeDriverManager().install())
                browser = webdriver.Chrome(service=service)
            except:
                # Fallback to default Chrome if webdriver-manager fails
                browser = webdriver.Chrome()
            
            try:
                # Login to LinkedIn (following the working example pattern)
                browser.get("https://www.linkedin.com/login")
                time.sleep(2)
                
                # Find and fill login form
                username_input = browser.find_element("id", "username")
                password_input = browser.find_element("id", "password")
                username_input.send_keys(linkedin_email)
                password_input.send_keys(linkedin_password)
                password_input.send_keys(Keys.RETURN)
                
                time.sleep(3)
                
                # Check for security challenges
                if "challenge" in browser.current_url or "checkpoint" in browser.current_url:
                    browser.quit()
                    return json.dumps({
                        "error": "LinkedIn security challenge detected",
                        "message": "LinkedIn requires additional verification. Please login manually once, then try again.",
                        "suggestion": "Try logging in to LinkedIn manually in a browser first to clear any security challenges.",
                        "fallback": "Using mock data for now",
                        "mock_data": self._generate_mock_linkedin_data(topic, max_posts)
                    })
                
                # Navigate to search results for the topic
                search_url = f"https://www.linkedin.com/search/results/content/?keywords={topic.replace(' ', '%20')}&origin=GLOBAL_SEARCH_HEADER&sortBy=date"
                browser.get(search_url)
                time.sleep(3)
                
                # Scroll to load more posts
                for _ in range(2):
                    browser.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    time.sleep(2)
                
                # Extract posts from page source
                posts_data = self._extract_posts_from_page(browser.page_source, max_posts)
                
                browser.quit()
                
                if not posts_data:
                    return json.dumps({
                        "note": "No posts found or access restricted",
                        "explanation": "Could not extract posts from LinkedIn search results. Using mock data.",
                        "fallback": "Using mock data for development",
                        "mock_data": self._generate_mock_linkedin_data(topic, max_posts)
                    })
                
                return json.dumps({
                    "topic": topic,
                    "posts_found": len(posts_data),
                    "posts": posts_data,
                    "scraped_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "source": "real_linkedin_data"
                })
                
            except Exception as scraping_error:
                browser.quit()
                return json.dumps({
                    "error": f"LinkedIn scraping failed: {str(scraping_error)}",
                    "message": "Could not scrape LinkedIn posts. Check your credentials and try again.",
                    "fallback": "Using mock data for development",
                    "mock_data": self._generate_mock_linkedin_data(topic, max_posts)
                })
                
        except Exception as e:
            return json.dumps({
                "error": f"Failed to initialize LinkedIn scraper: {str(e)}",
                "fallback": "Using mock data for development",
                "mock_data": self._generate_mock_linkedin_data(topic, max_posts)
            })
    
    def _extract_posts_from_page(self, page_source: str, max_posts: int) -> List[Dict[str, Any]]:
        """Extract posts from LinkedIn page source using BeautifulSoup."""
        try:
            soup = BeautifulSoup(page_source, 'html.parser')
            posts_data = []
            
            # Find post containers - try multiple selectors
            post_selectors = [
                '.feed-shared-update-v2',
                '.feed-shared-update',
                '[data-id]',
                '.update-components-text'
            ]
            
            posts = []
            for selector in post_selectors:
                posts = soup.select(selector)
                if posts:
                    break
            
            for i, post in enumerate(posts[:max_posts]):
                try:
                    post_data = self._extract_single_post_data(post)
                    if post_data and post_data.get('content'):
                        posts_data.append(post_data)
                        
                    if len(posts_data) >= max_posts:
                        break
                        
                except Exception as e:
                    continue
            
            return posts_data
            
        except Exception as e:
            return []
    
    def _extract_single_post_data(self, post_element) -> Dict[str, Any]:
        """Extract data from a single post element."""
        try:
            post_data = {}
            
            # Extract post content - try multiple selectors
            content_selectors = [
                '.feed-shared-text__text-view',
                '.feed-shared-text',
                '.update-components-text__text-view',
                '.attributed-text-segment-list__content',
                '[data-test-id="main-feed-activity-card__commentary"]'
            ]
            
            content = ""
            for selector in content_selectors:
                content_elem = post_element.select_one(selector)
                if content_elem:
                    content = content_elem.get_text(strip=True)
                    if content:
                        break
            
            post_data["content"] = content if content else "Content not accessible"
            
            # Extract author name
            author_selectors = [
                '.feed-shared-actor__name',
                '.feed-shared-actor__name-link',
                '.app-aware-link',
                '.update-components-actor__name'
            ]
            
            author = ""
            for selector in author_selectors:
                author_elem = post_element.select_one(selector)
                if author_elem:
                    author = author_elem.get_text(strip=True)
                    if author:
                        break
            
            post_data["author"] = author if author else "Unknown Author"
            
            # Extract engagement metrics
            likes_selectors = [
                '.social-counts-reactions__count',
                '[data-test-id="social-counts-reactions"]',
                '.social-counts-reactions'
            ]
            
            likes = "0"
            for selector in likes_selectors:
                likes_elem = post_element.select_one(selector)
                if likes_elem:
                    likes = likes_elem.get_text(strip=True)
                    if likes:
                        break
            
            post_data["likes"] = likes
            
            # Extract comments
            comments_selectors = [
                '.social-counts-comments__count',
                '[data-test-id="social-counts-comments"]',
                '.social-counts-comments'
            ]
            
            comments = "0"
            for selector in comments_selectors:
                comments_elem = post_element.select_one(selector)
                if comments_elem:
                    comments = comments_elem.get_text(strip=True)
                    if comments:
                        break
            
            post_data["comments"] = comments
            
            # Extract timestamp
            time_selectors = [
                '.feed-shared-actor__sub-description',
                '.update-components-actor__sub-description',
                'time'
            ]
            
            timestamp = ""
            for selector in time_selectors:
                time_elem = post_element.select_one(selector)
                if time_elem:
                    timestamp = time_elem.get_text(strip=True)
                    if timestamp:
                        break
            
            post_data["timestamp"] = timestamp if timestamp else "Unknown"
            
            # Only return if we have meaningful content
            if post_data["content"] and post_data["content"] != "Content not accessible" and len(post_data["content"]) > 20:
                return post_data
            else:
                return None
                
        except Exception as e:
            return None
    
    def _generate_mock_linkedin_data(self, topic: str, max_posts: int) -> List[Dict[str, Any]]:
        """Generate mock LinkedIn data for development/testing purposes."""
        mock_posts = []
        
        sample_posts = [
            {
                "content": f"Just had an incredible breakthrough with {topic}! The possibilities are endless when you combine innovation with dedication. Here's what I learned... 🚀",
                "author": "Tech Innovator",
                "likes": "245 likes",
                "comments": "23 comments",
                "engagement_rate": "high"
            },
            {
                "content": f"After 5 years working with {topic}, I can confidently say this is the future. Here are 3 key insights that changed my perspective:",
                "author": "Industry Expert", 
                "likes": "189 likes",
                "comments": "31 comments",
                "engagement_rate": "medium"
            },
            {
                "content": f"Unpopular opinion: {topic} is overhyped. But here's why that might actually be a good thing for early adopters...",
                "author": "Contrarian Thinker",
                "likes": "156 likes", 
                "comments": "67 comments",
                "engagement_rate": "high"
            },
            {
                "content": f"Just implemented {topic} at our company. Results after 30 days: 📈 40% improvement in efficiency. Here's our playbook:",
                "author": "CEO & Founder",
                "likes": "312 likes",
                "comments": "45 comments", 
                "engagement_rate": "very_high"
            },
            {
                "content": f"The biggest mistake people make with {topic}? They focus on the technology instead of the problem it solves. Let me explain...",
                "author": "Strategy Consultant",
                "likes": "98 likes",
                "comments": "19 comments",
                "engagement_rate": "medium"
            }
        ]
        
        for i in range(min(max_posts, len(sample_posts))):
            mock_posts.append({
                **sample_posts[i],
                "post_id": f"mock_post_{i+1}",
                "timestamp": f"2024-09-{20-i}",
                "hashtags": [f"#{topic.replace(' ', '')}", "#Innovation", "#Technology", "#Business"],
                "is_mock_data": True
            })
        
        return mock_posts
