# LinkedIn Post Generation Crew 🚀

An intelligent multi-agent AI system that automatically generates authentic LinkedIn posts by analyzing your personal writing style and conducting web research. Powered by [crewAI](https://crewai.com) and designed to create content that matches your unique voice.

## 🎯 What This Crew Does

This AI crew consists of 4 specialized agents working together:

1. **Personal Writing Style Analyst** - Analyzes your own LinkedIn posts to understand your authentic voice and content patterns
2. **Web Research Agent** - Conducts comprehensive web research using DuckDuckGo for current trends and data  
3. **Authentic Content Creator** - Creates genuine posts that maintain your voice while incorporating research insights
4. **Humanizer Agent** - Refines the content using a specific writing style while preserving your authentic voice

## 🛠️ Quick Setup

### Prerequisites
Ensure you have Python >=3.10 <3.14 installed on your system.

```bash
# Clone the repository
git clone <your-repo-url>
cd linkedin_post

# Install CrewAI CLI (if not already installed)
pip install crewai[tools]

# Create virtual environment and install dependencies
crewai install
```

That's it! CrewAI automatically:
- Creates a virtual environment
- Installs all dependencies from `pyproject.toml`
- Sets up the project structure

## 🔑 Environment Configuration

Create a `.env` file in the project root:

```bash
# Required: OpenAI API Key
OPENAI_API_KEY=your_openai_api_key_here

# Required: LinkedIn Authentication (for analyzing your own posts)
LINKEDIN_EMAIL=your_linkedin_email@example.com
LINKEDIN_PASSWORD=your_linkedin_password
LINKEDIN_PROFILE_NAME=your_linkedin_profile_name
```

**Note**: The `LINKEDIN_PROFILE_NAME` is the part of your LinkedIn URL after `/in/`. For example, if your LinkedIn profile is `https://www.linkedin.com/in/john-smith-123/`, then your profile name is `john-smith-123`.

## 🚀 Running the Crew

### Step 1: Customize Your Prompt
Edit `src/linkedin_post/main.py` and replace the prompt on line 31:

```python
prompt = "Your custom LinkedIn post prompt here"
```

**Good prompt examples:**
- `"Write about my journey learning multi-agent AI systems, focusing on challenges and breakthroughs"`
- `"Share insights about AI automation in business with practical examples"`
- `"Create a post about building this LinkedIn crew, highlighting technical lessons learned"`

### Step 2: Run the Crew
```bash
crewai run
```

The crew will:
1. Analyze trending LinkedIn posts about your topic
2. Research current trends and data on the web
3. Create a compelling LinkedIn post
4. Humanize it for authentic engagement
5. Save the final post to `linkedin_post.md`

## 📝 Customization

You can customize the crew behavior by modifying:

- **`src/linkedin_post/config/agents.yaml`** - Define agent personalities and roles
- **`src/linkedin_post/config/tasks.yaml`** - Configure tasks and expected outputs  
- **`src/linkedin_post/main.py`** - Change the topic or add custom inputs
- **`src/linkedin_post/crew.py`** - Add custom tools or modify agent workflows

### Customizing Your Prompts

The prompt is clearly marked in `src/linkedin_post/main.py` around line 31. Simply edit it with your specific requirements:

```python
# Replace this line with your custom prompt
prompt = "Write about my journey getting into multi-agent AI systems, focusing on the challenges I overcame and how this technology is changing the future of work"
```

**Pro Tips for Better Prompts:**
- ✅ Be specific about the angle/perspective
- ✅ Include the type of content (personal story, insights, tutorial, etc.)
- ✅ Mention your target audience 
- ✅ Add any specific points you want covered
- ✅ The more detailed, the better the output!

## 🔧 Project Structure

```
linkedin_post/
├── src/linkedin_post/
│   ├── config/
│   │   ├── agents.yaml      # Agent definitions
│   │   └── tasks.yaml       # Task configurations  
│   ├── tools/
│   │   ├── linkedin_scraper.py  # LinkedIn scraping tool
│   │   └── web_research.py      # Web research tool
│   ├── crew.py             # Main crew orchestration
│   └── main.py             # Entry point
├── pyproject.toml          # Dependencies and project config
└── README.md              # This file
```

## 🤖 How It Works

1. **LinkedIn Analysis**: Scrapes trending posts (with fallback mock data due to LinkedIn's restrictions)
2. **Web Research**: Uses DuckDuckGo to find current trends, statistics, and expert opinions
3. **Content Creation**: Combines insights to create structured, engaging LinkedIn posts
4. **Humanization**: Transforms AI-generated content into authentic, conversational posts

## 🚨 Important Notes

- **LinkedIn Scraping**: Add your LinkedIn credentials to `.env` for real post scraping, or use mock data as fallback
- **API Keys**: You'll need an OpenAI API key to run the crew
- **Python Version**: Requires Python 3.10-3.13

### LinkedIn Authentication & Real Post Scraping

The LinkedIn Scraper Agent can access real LinkedIn posts with authentication:

**Option 1: Real LinkedIn Posts (Recommended)**
- Add your LinkedIn credentials to the `.env` file
- The tool will automatically login and scrape real trending posts
- Provides authentic engagement data and content patterns

**Option 2: Mock Data (Fallback)**
- If no credentials provided, uses realistic mock data
- Mock data reflects current LinkedIn trends and engagement patterns
- Still produces high-quality content since Web Research provides real data

**Important Notes:**
- Use your own LinkedIn account credentials
- The tool respects LinkedIn's rate limits and uses anti-detection measures
- If LinkedIn requires additional verification, you may need to login manually once
- Your credentials are only used locally and never stored or transmitted

## 🛠️ Dependencies

- **crewAI**: Multi-agent framework
- **LangChain Community**: DuckDuckGo search integration  
- **Selenium**: Web scraping capabilities
- **OpenAI**: LLM provider

## 📈 Example Output

The crew generates a complete LinkedIn post with:
- Attention-grabbing hook
- Data-driven insights  
- Personal perspective
- Relevant hashtags
- Call-to-action
- Authentic, human-like tone

## 🤝 Contributing

This project showcases multi-agent AI systems in action. Feel free to:
- Fork and customize for your needs
- Submit issues or suggestions
- Share your generated posts!

## 📄 License

Open source - feel free to use and modify!
