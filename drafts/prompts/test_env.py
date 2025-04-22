from dotenv import load_dotenv
import os

load_dotenv(dotenv_path=".env")  # explicitly specify the .env file path

api_key = os.getenv("OPENROUTER_API_KEY")

print(f"My API key is: {api_key}")
