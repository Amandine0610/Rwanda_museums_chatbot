import os
from dotenv import load_dotenv
import openai

def test_key():
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")
    
    if not api_key:
        print("ERROR: No OPENAI_API_KEY found in .env file.")
        return

    print(f"Checking key starting with: {api_key[:8]}...")
    
    client = openai.OpenAI(api_key=api_key)
    
    try:
        # Simple models list call to check auth
        client.models.list()
        print("SUCCESS: The API key is valid and can connect to OpenAI!")
        
        # Try a small completion to check quota/billing
        print("Testing chat completion (quota check)...")
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": "Say hello"}],
            max_tokens=5
        )
        print(f"SUCCESS: Chat completion works! Response: {response.choices[0].message.content}")
        
    except openai.AuthenticationError:
        print("ERROR: Authentication failed. Your API key is invalid.")
    except openai.RateLimitError:
        print("ERROR: Rate limit reached or No Credits. Check your billing/usage on OpenAI dashboard.")
    except openai.NotFoundError:
        print("ERROR: Model 'gpt-4o-mini' not found or not accessible with this key.")
    except Exception as e:
        print(f"ERROR: An unexpected error occurred: {e}")

if __name__ == "__main__":
    test_key()
