import os
import random
from datetime import datetime
import chromadb

print("[SYSTEM]: Initializing ChromaDB Long-Term Memory Core...")

# Ensure Windows builds the folder safely in the user profile
MEMORY_PATH = os.path.join(os.environ.get('USERPROFILE', ''), "Vance_Memory_Core")
os.makedirs(MEMORY_PATH, exist_ok=True) 

# Initialize Persistent Vector Database
chroma_client = chromadb.PersistentClient(path=MEMORY_PATH)
memory_collection = chroma_client.get_or_create_collection(name="vance_archives")

# Short-term session RAM
conversation_history = []

def _save_to_chroma(u_text, r_text):
    """Safely locks a memory into the vault with anti-duplication IDs."""
    try:
        # Added a random integer to the ID to completely prevent duplication errors
        doc_id = str(datetime.now().timestamp()) + str(random.randint(1000, 9999))
        memory_collection.add(
            documents=[f"Context: {u_text} | Fact: {r_text}"], 
            ids=[doc_id]
        )
        print(f"[VANCE INTERNAL]: Memory safely locked in the vault.")
    except Exception as e: 
        print(f"[MEMORY SAVE ERROR]: {e}")

def retrieve_long_term_memory(query):
    """Fetches the top 3 most relevant past memories based on the user's query."""
    try:
        db_size = memory_collection.count()
        if db_size == 0: 
            return "No past memories found."
        
        fetch_count = min(3, db_size) 
        
        results = memory_collection.query(query_texts=[query], n_results=fetch_count)
        if results['documents'] and results['documents'][0]:
            extracted_memories = "\n".join(results['documents'][0])
            # Vance thinks in silence, returning context directly to the brain
            return extracted_memories
            
        return "No relevant past memories found."
    except Exception as e: 
        print(f"[MEMORY RETRIEVAL ERROR]: {e}")
        return "Memory retrieval failed."

def update_memory(user_text, reply_text):
    """Updates active conversation context and commits to long-term storage."""
    global conversation_history
    
    # 1. Append to short-term session RAM
    conversation_history.append({"role": "user", "content": user_text})
    conversation_history.append({"role": "assistant", "content": reply_text})
    
    # --- THE SNOWBALL PATCH ---
    # Restrict short-term memory to the last 10 messages (5 interactions)
    # to prevent infinite token burn.
    if len(conversation_history) > 10:
        conversation_history = conversation_history[-10:]
        
    # 2. Save everything to the permanent ChromaDB vault
    _save_to_chroma(user_text, reply_text)

def get_conversation_history():
    return conversation_history