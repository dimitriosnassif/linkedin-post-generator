import os
import time
from crewai.tools import BaseTool
from typing import Type, List, Dict, Any
from pydantic import BaseModel, Field
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import json
from bs4 import BeautifulSoup


class LinkedInScraperInput(BaseModel):
    """Input schema for LinkedIn Scraper."""
    topic: str = Field(..., description="The topic to search for on LinkedIn")
    max_posts: int = Field(default=10, description="Maximum number of posts to scrape")


class LinkedinToolException(Exception):
    def __init__(self):
        super().__init__("You need to set the LINKEDIN_EMAIL, LINKEDIN_PASSWORD and LINKEDIN_PROFILE_NAME env variables")


class LinkedInScraperTool(BaseTool):
    name: str = "LinkedIn Post Scraper"
    description: str = (
        "Scrapes the user's own LinkedIn posts to analyze their writing style and create content that matches their voice. "
        "Returns post content, engagement metrics, and writing patterns. "
        "Note: This tool requires LinkedIn login credentials and profile name to be set as environment variables."
    )
    args_schema: Type[BaseModel] = LinkedInScraperInput

    def _run(self, topic: str, max_posts: int = 10) -> str:
        """
        Scrape user's own LinkedIn posts to analyze their writing style.
        
        Args:
            topic: The topic to research (used for context)
            max_posts: Maximum number of posts to analyze
            
        Returns:
            JSON string containing user's posts and writing style analysis
        """
        try:
            return self._scrape_linkedin_posts_fn(topic, max_posts)
        except LinkedinToolException as e:
            return json.dumps({
                "error": str(e),
                "message": "Please add LINKEDIN_EMAIL, LINKEDIN_PASSWORD, and LINKEDIN_PROFILE_NAME to your .env file to analyze your own posts",
                "fallback": "Using mock data for development",
                "mock_data": self._generate_mock_user_posts(topic, max_posts)
            })
        except Exception as e:
            return json.dumps({
                "error": f"Failed to scrape LinkedIn posts: {str(e)}",
                "fallback": "Using mock data for development", 
                "mock_data": self._generate_mock_user_posts(topic, max_posts)
            })

    def _scrape_linkedin_posts_fn(self, topic: str, max_posts: int) -> str:
        """
        Scrape the user's own LinkedIn posts
        """
        linkedin_username = os.environ.get("LINKEDIN_EMAIL")
        linkedin_password = os.environ.get("LINKEDIN_PASSWORD")
        linkedin_profile_name = os.environ.get("LINKEDIN_PROFILE_NAME")

        if not (linkedin_username and linkedin_password and linkedin_profile_name):
            raise LinkedinToolException()

        browser = webdriver.Chrome()
        
        try:
            browser.get("https://www.linkedin.com/login")

            username_input = browser.find_element("id", "username")
            password_input = browser.find_element("id", "password")
            username_input.send_keys(linkedin_username)
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
                    "mock_data": self._generate_mock_user_posts(topic, max_posts)
                })

            browser.get(f"https://www.linkedin.com/in/{linkedin_profile_name}/recent-activity/all/")

            for _ in range(2):
                browser.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)

            posts = self._get_linkedin_posts(browser.page_source)
            browser.quit()

            # Return the latest posts for analysis
            user_posts = posts[:max_posts] if posts else []
            
            if not user_posts:
                return json.dumps({
                    "note": "No posts found on your profile",
                    "explanation": "Could not extract posts from your LinkedIn profile. Using mock data.",
                    "fallback": "Using mock data for development",
                    "mock_data": self._generate_mock_user_posts(topic, max_posts)
                })

            # Analyze writing style from user's posts
            writing_style_analysis = self._analyze_writing_style(user_posts)

            return json.dumps({
                "topic": topic,
                "posts_found": len(user_posts),
                "user_posts": user_posts,
                "writing_style_analysis": writing_style_analysis,
                "scraped_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                "source": "user_linkedin_profile",
                "profile": linkedin_profile_name
            })
            
        except Exception as e:
            browser.quit()
            raise e

    def _get_linkedin_posts(self, page_source: str) -> List[Dict[str, Any]]:
        """Extract posts from LinkedIn profile page using BeautifulSoup."""
        try:
            soup = BeautifulSoup(page_source, 'html.parser')
            posts_data = []
            
            # Find post containers - try multiple selectors for profile posts
            post_selectors = [
                '.feed-shared-update-v2',
                '.profile-creator-shared-feed-update__container',
                '.occludable-update',
                '[data-urn*="activity"]',
                '.feed-shared-update'
            ]
            
            posts = []
            for selector in post_selectors:
                posts = soup.select(selector)
                if posts:
                    break
            
            for post in posts:
                try:
                    post_data = self._extract_single_post_data(post)
                    if post_data and post_data.get('content') and len(post_data['content']) > 50:
                        posts_data.append(post_data)
                        
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
                '[data-test-id="main-feed-activity-card__commentary"]',
                '.profile-creator-shared-feed-update__description'
            ]
            
            content = ""
            for selector in content_selectors:
                content_elem = post_element.select_one(selector)
                if content_elem:
                    content = content_elem.get_text(strip=True)
                    if content and len(content) > 20:
                        break
            
            if not content:
                return None
                
            post_data["content"] = content
            
            # Extract engagement metrics
            likes_selectors = [
                '.social-counts-reactions__count',
                '[data-test-id="social-counts-reactions"]',
                '.social-counts-reactions',
                '.reactions-count'
            ]
            
            likes = "0"
            for selector in likes_selectors:
                likes_elem = post_element.select_one(selector)
                if likes_elem:
                    likes_text = likes_elem.get_text(strip=True)
                    if likes_text:
                        likes = likes_text
                        break
            
            post_data["likes"] = likes
            
            # Extract comments count
            comments_selectors = [
                '.social-counts-comments__count',
                '[data-test-id="social-counts-comments"]',
                '.social-counts-comments',
                '.comments-count'
            ]
            
            comments = "0"
            for selector in comments_selectors:
                comments_elem = post_element.select_one(selector)
                if comments_elem:
                    comments_text = comments_elem.get_text(strip=True)
                    if comments_text:
                        comments = comments_text
                        break
            
            post_data["comments"] = comments
            
            # Extract timestamp
            time_selectors = [
                '.feed-shared-actor__sub-description',
                '.update-components-actor__sub-description',
                'time',
                '.profile-creator-shared-feed-update__meta'
            ]
            
            timestamp = ""
            for selector in time_selectors:
                time_elem = post_element.select_one(selector)
                if time_elem:
                    timestamp = time_elem.get_text(strip=True)
                    if timestamp:
                        break
            
            post_data["timestamp"] = timestamp if timestamp else "Unknown"
            
            return post_data
                
        except Exception as e:
            return None

    def _analyze_writing_style(self, posts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze the user's writing style from their posts."""
        if not posts:
            return {"error": "No posts to analyze"}
        
        analysis = {
            "total_posts_analyzed": len(posts),
            "writing_patterns": {
                "average_post_length": sum(len(post["content"]) for post in posts) / len(posts),
                "uses_emojis": any("🚀" in post["content"] or "💡" in post["content"] or "🎯" in post["content"] for post in posts),
                "uses_questions": any("?" in post["content"] for post in posts),
                "uses_lists": any("•" in post["content"] or "-" in post["content"] or "1." in post["content"] for post in posts),
                "personal_tone": any(word in post["content"].lower() for post in posts for word in ["i", "my", "me", "personally"]),
                "professional_tone": any(word in post["content"].lower() for post in posts for word in ["team", "company", "project", "business"])
            },
            "engagement_patterns": {
                "high_engagement_posts": [post for post in posts if self._extract_number(post.get("likes", "0")) > 50],
                "common_themes": self._extract_common_themes(posts)
            },
            "style_recommendations": [
                "Maintain your authentic voice and personal experiences",
                "Keep using your successful content structures",
                "Continue your engaging storytelling approach"
            ]
        }
        
        return analysis

    def _extract_number(self, text: str) -> int:
        """Extract number from engagement text like '245 likes'."""
        try:
            import re
            numbers = re.findall(r'\d+', str(text))
            return int(numbers[0]) if numbers else 0
        except:
            return 0

    def _extract_common_themes(self, posts: List[Dict[str, Any]]) -> List[str]:
        """Extract common themes from posts."""
        all_text = " ".join(post["content"].lower() for post in posts)
        
        # Common professional themes
        themes = []
        theme_keywords = {
            "technology": ["ai", "tech", "innovation", "digital", "automation"],
            "leadership": ["team", "leadership", "management", "strategy"],
            "learning": ["learn", "growth", "development", "skill", "knowledge"],
            "career": ["career", "job", "work", "professional", "experience"]
        }
        
        for theme, keywords in theme_keywords.items():
            if any(keyword in all_text for keyword in keywords):
                themes.append(theme)
        
        return themes[:3]  # Return top 3 themes

    def _generate_mock_user_posts(self, topic: str, max_posts: int) -> List[Dict[str, Any]]:
        """Generate mock user posts for development/testing purposes."""
        mock_posts = [
            {
                "content": f"Been diving deep into {topic} lately and the learning curve has been intense! Here are 3 key insights I've gained so far...",
                "likes": "89 likes",
                "comments": "12 comments",
                "timestamp": "2 days ago"
            },
            {
                "content": f"Unpopular opinion: Most people approach {topic} completely wrong. Here's what I learned after months of trial and error:",
                "likes": "156 likes", 
                "comments": "34 comments",
                "timestamp": "1 week ago"
            },
            {
                "content": f"Just wrapped up an amazing project involving {topic}. The results exceeded all expectations! 🚀 Key takeaways:",
                "likes": "203 likes",
                "comments": "28 comments", 
                "timestamp": "2 weeks ago"
            }
        ]
        
        return mock_posts[:max_posts]