import os


mem0_config = {
    "llm": {
        "provider": "openai",
        "config": {
            "model": os.getenv('MEM0_MODEL_CHOICE', 'gpt-4o-mini')
        }
    },
    
    "vector_store": {
        "provider": "supabase",
        "config": {
            "connection_string": os.environ['SUPABASE_DB_URL'],
            "collection_name": "memories"
        }
    }    
}