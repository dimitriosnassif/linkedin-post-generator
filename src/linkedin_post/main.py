#!/usr/bin/env python
import sys
import warnings

from datetime import datetime

from linkedin_post.crew import LinkedinPost

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")

# This main file is intended to be a way for you to run your
# crew locally, so refrain from adding unnecessary logic into this file.
# Replace with inputs you want to test with, it will automatically
# interpolate any tasks and agents information

def run():
    """
    Run the crew with a custom prompt.
    """
    # ========================================
    # 📝 CUSTOMIZE YOUR LINKEDIN POST PROMPT HERE
    # ========================================
    # Replace the prompt below with your own detailed prompt for the LinkedIn post you want to generate.
    # The more specific and detailed your prompt, the better the generated content will be!
    
    # Examples of good prompts:
    # "Write about my journey learning multi-agent AI systems, focusing on the challenges I overcame and key breakthroughs"
    # "Share insights about the future of AI automation in business, including practical applications and potential concerns"
    # "Create a post about building this LinkedIn post generation crew, highlighting the technical challenges and lessons learned"
    
    prompt = "Write about my journey getting into multi-agent AI systems, focusing on the challenges I overcame and how this technology is changing the future of work"
    
    # ========================================
    # Don't edit below this line
    # ========================================
    
    inputs = {
        'topic': prompt,
        'current_year': str(datetime.now().year)
    }
    
    print("🤖 LinkedIn Post Generation Crew")
    print("=" * 50)
    print(f"🚀 Generating LinkedIn post with prompt:")
    print(f"'{prompt}'")
    print("=" * 50)
    
    try:
        LinkedinPost().crew().kickoff(inputs=inputs)
        print("\n✅ LinkedIn post generated successfully!")
        print("Check the 'linkedin_post.md' file for your generated content.")
    except Exception as e:
        raise Exception(f"An error occurred while running the crew: {e}")


def train():
    """
    Train the crew for a given number of iterations.
    """
    if len(sys.argv) < 4:
        print("Usage: crewai train <n_iterations> <filename> '<prompt>'")
        print("Example: crewai train 3 training_data.json 'Write about AI trends'")
        sys.exit(1)
    
    prompt = sys.argv[3] if len(sys.argv) > 3 else "multi-agent AI systems"
    
    inputs = {
        "topic": prompt,
        'current_year': str(datetime.now().year)
    }
    try:
        LinkedinPost().crew().train(n_iterations=int(sys.argv[1]), filename=sys.argv[2], inputs=inputs)

    except Exception as e:
        raise Exception(f"An error occurred while training the crew: {e}")

def replay():
    """
    Replay the crew execution from a specific task.
    """
    try:
        LinkedinPost().crew().replay(task_id=sys.argv[1])

    except Exception as e:
        raise Exception(f"An error occurred while replaying the crew: {e}")

def test():
    """
    Test the crew execution and returns the results.
    """
    if len(sys.argv) < 4:
        print("Usage: crewai test <n_iterations> <eval_llm> '<prompt>'")
        print("Example: crewai test 2 gpt-4 'Write about AI trends'")
        sys.exit(1)
    
    prompt = sys.argv[3] if len(sys.argv) > 3 else "multi-agent AI systems"
    
    inputs = {
        "topic": prompt,
        "current_year": str(datetime.now().year)
    }
    
    try:
        LinkedinPost().crew().test(n_iterations=int(sys.argv[1]), eval_llm=sys.argv[2], inputs=inputs)

    except Exception as e:
        raise Exception(f"An error occurred while testing the crew: {e}")
