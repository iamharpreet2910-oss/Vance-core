import os
import ctypes
import base64
from io import BytesIO
from PIL import ImageGrab
import psutil
import speech_recognition as sr
import tkinter as tk
from config import groq_client

# --- OPTICAL NERVE CONFIG ---
import pytesseract
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def get_active_context():
    """Zero-RAM Context Hook: Silently reads the active Windows foreground process."""
    try:
        hwnd = ctypes.windll.user32.GetForegroundWindow()
        length = ctypes.windll.user32.GetWindowTextLengthW(hwnd)
        buf = ctypes.create_unicode_buffer(length + 1)
        ctypes.windll.user32.GetWindowTextW(hwnd, buf, length + 1)
        title = buf.value
        return title if title else "Desktop / Idle"
    except Exception as e:
        print(f"[CONTEXT ERROR]: {e}")
        return "Unknown"

def capture_screen_base64():
    """Captures and compresses the optical feed for the Cloud VLM."""
    print("[VANCE INTERNAL]: Capturing screen and encoding for Cloud VLM...")
    try:
        screenshot = ImageGrab.grab()
        # Compress to 720p to save internet bandwidth and API limits
        screenshot.thumbnail((1280, 720)) 
        
        # Convert the image directly in RAM to a Base64 string
        buffered = BytesIO()
        screenshot.save(buffered, format="JPEG", quality=80)
        img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
        return img_str
    except Exception as e: 
        return f"Optical failure: {e}"

def scan_system_processes():
    """Scans active process tree for RAM bottlenecks."""
    print("[VANCE INTERNAL]: Scanning active process tree...")
    try:
        processes = []
        for proc in psutil.process_iter(['name', 'memory_percent']):
            try:
                name = proc.info['name']
                mem = proc.info['memory_percent']
                if name and mem is not None and mem > 0.1:
                    processes.append((name, mem))
            except: 
                pass
            
        processes.sort(key=lambda x: x[1], reverse=True)
        top_procs = processes[:15]
        
        if not top_procs: return "No processes detected."
        
        report = ", ".join([f"{p[0]} ({p[1]:.1f}%)" for p in top_procs])
        return f"Top RAM Processes: {report}"
    except Exception as e:
        return f"Process scan failed: {e}"     

def read_clipboard():
    """Accesses the system clipboard natively."""
    print("[VANCE INTERNAL]: Accessing system clipboard...")
    try:
        root = tk.Tk()
        root.withdraw() 
        clip_text = root.clipboard_get()
        root.destroy()
        if not clip_text.strip(): return "The clipboard is empty."
        return clip_text[:1500]
    except Exception: 
        return "Clipboard is empty or contains non-text data."

def listen_for_command(vance_ear):
    """Listens for commands and processes audio entirely in RAM via Groq Whisper."""
    vance_ear.dynamic_energy_threshold = True 
    with sr.Microphone() as source:
        print("\n[VANCE]: (Awaiting your command...)")
        try:
            audio = vance_ear.listen(source, timeout=None, phrase_time_limit=15)
            print("[SYSTEM]: Voice detected! Sending to Groq Whisper...")
            
            # THE FIX: Bypassing the hard drive. Pushing audio bytes directly to the API.
            audio_data = audio.get_wav_data()
            virtual_file = ("in_memory.wav", audio_data, "audio/wav")
            
            text = groq_client.audio.transcriptions.create(
                file=virtual_file, 
                model="whisper-large-v3", 
                prompt="Vance, Sir, Harpreet, Python, code, script.",
                response_format="text"
            ).strip()
                
            phantom_phrases = ["thank you.", "i'm sorry.", "thank you", "i'm sorry", "subscribe", "thanks for watching", "you.", "bye.", "you", "."]
            if not text or text.lower() in phantom_phrases or len(text) < 3: 
                return None
            
            print(f"[HARPREET]: {text}")
            return text.lower()
            
        except sr.WaitTimeoutError: 
            return None
        except Exception as e: 
            print(f"\n[DIAGNOSTIC EAR ERROR]: {e}")
            return None