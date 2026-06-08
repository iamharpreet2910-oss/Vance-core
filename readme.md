# ⚡ VANCE // CORE
**Autonomous Multi-Modal Digital Butler**

Vance is a highly asynchronous, multi-modal AI agent built to execute complex OS-level commands, maintain persistent long-term memory, and physically interact with the Windows environment through an autonomous vision-language loop. 

Unlike standard conversational wrappers, Vance operates as a localized digital butler. He possesses "eyes" (screen capture + OCR), "hands" (PyAutoGUI + Playwright), and a "dual-brain" architecture that routes lightweight tasks to fast models and complex logic to heavy-compute servers in real-time.

---

## 🏗️ Core Architecture

The system is fully modularized for enterprise-grade scalability and rapid feature deployment:

* **`main.py` (The Central Nervous System):** Orchestrates the asynchronous `asyncio` brain loop alongside a non-blocking `CustomTkinter` UI daemon. Handles the bulletproof JSON intent parser.
* **`config.py` (The Routing Engine):** Secures environment variables and manages the Dual-Brain LLM routing between standard and high-compute inference states.
* **`memory_core.py` (The Vault):** A persistent ChromaDB vector database. Vance continuously indexes interactions, using custom deduplication logic and a short-term rolling context window to prevent token burn.
* **`senses.py` (The Input Layer):** Houses the in-memory Whisper transcription pipeline, optical screen-capture encoders, and a custom **Zero-RAM Context Hook** that reads active Windows foreground processes via `ctypes`.
* **`hands.py` (The Output Layer):** Executes physical agency. Features an agentic web-surfer, local file traversal, and an aggressive fuzzy-matching OCR mouse controller for dynamic UI targeting.

---

## 🚀 Key Capabilities

* **Dual-Brain Routing:** Seamlessly shifts between Llama-3.1-8B for rapid, conversational OS commands and Llama-3.3-70B for strict, heavy-compute coding logic.
* **Agentic Vision Loops:** Capable of analyzing the screen via Llama-4-Scout, determining the necessary UI target, and engaging Tesseract OCR to physically move the cursor and click the objective.
* **Zero-RAM Context:** Vance silently knows what application or window you are actively looking at without continuously burning background memory.
* **In-Memory Audio Processing:** Bypasses disk I/O bottlenecks by capturing microphone data into a `BytesIO` buffer, sending it directly to Groq Whisper for near-instant transcription.
* **Bare-Metal OS Control:** Granular control over volume, media playback, specific application termination, system process scanning, and WhatsApp integration.

---

## 🛠️ Setup & Installation

### 1. Prerequisites
* **Python 3.10+**
* **Tesseract OCR:** Must be installed on your Windows machine. The script expects the executable at: `C:\Program Files\Tesseract-OCR\tesseract.exe`.

### 2. Environment Variables
Create a `.env` file in the root directory. **Do not commit this file.**

```env
HF_TOKEN=your_huggingface_token_here
GROQ_API_KEY=your_groq_api_key_here