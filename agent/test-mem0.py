import asyncio
from dotenv import load_dotenv
from mem0 import AsyncMemoryClient

load_dotenv()

mem0_client = AsyncMemoryClient()

async def fetch_recent_memories():
    results = await mem0_client.search(
        query="Can you tell me what do I like to eat?",  
        user_id="default_user",
        limit=5
    )
    print(results)

asyncio.run(fetch_recent_memories())
