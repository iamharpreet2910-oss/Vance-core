import os
from dotenv import load_dotenv
from groq import Groq
from openai import OpenAI

# Initialize environment variables
load_dotenv()

# --- SECURITY PROTOCOL ---
# We raise a hard error if the token is missing to prevent silent failures
HF_TOKEN = os.environ.get("HF_TOKEN")
if not HF_TOKEN:
    raise SystemExit("[SECURITY ALERT]: HF_TOKEN missing from .env file. System halted.")

GROQ_TOKEN = os.environ.get("GROQ_API_KEY")
if not GROQ_TOKEN:
    raise SystemExit("[SECURITY ALERT]: GROQ_API_KEY missing from .env file. System halted.")

# --- DUAL-BRAIN CLIENT INITIALIZATION ---
# Fast Compute (Llama 3 8B / 3.3 70B via Groq)
groq_client = Groq(api_key=GROQ_TOKEN)

# High-Speed Inference Router (via Hugging Face)
hf_client = OpenAI(
    base_url="https://router.huggingface.co/hf-inference/v1", 
    api_key=HF_TOKEN
)

# Global State Tracker
vance_mode = "standard" 

def get_vance_mode():
    return vance_mode

def set_vance_mode(mode):
    global vance_mode
    vance_mode = mode