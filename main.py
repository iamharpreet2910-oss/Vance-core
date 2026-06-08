import os
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
import json
import asyncio
import random
import webbrowser
import urllib.parse
import speech_recognition as sr
import edge_tts
import psutil
import keyboard
import requests
from datetime import datetime
import pygame 
import time 
import csv 
import pyautogui
import tkinter as tk 
import threading
import customtkinter as ctk 
import math

# --- VANCE MODULAR ORGANS ---
from config import groq_client, hf_client, get_vance_mode, set_vance_mode
from memory_core import retrieve_long_term_memory, update_memory, _save_to_chroma, get_conversation_history
from senses import get_active_context, capture_screen_base64, scan_system_processes, read_clipboard, listen_for_command
from hands import click_on_text, agentic_web_surf, scrape_webpage, find_and_open_file, _blocking_file_search

# Global Audio Engine
pygame.mixer.init()
vance_ear = sr.Recognizer()
vance_ear.pause_threshold = 1.5 

# --- GUI ARCHITECTURE ---
app = None
console_box = None
status_label = None
canvas = None
bars = []
phase = 0

def vance_log(text):
    """Central logging system. Prints to console, updates GUI, and writes to a permanent debug file."""
    print(text) 
    
    # THE BUG FIX: Structured logging prevents silent failure blindness
    try:
        with open("vance_debug.log", "a", encoding="utf-8") as f:
            f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {text}\n")
    except:
        pass

    if console_box:
        console_box.configure(state="normal")
        console_box.insert("end", str(text) + "\n\n")
        console_box.see("end")
        console_box.configure(state="disabled")
        app.update()

def animate_hud():
    global phase
    try:
        cpu = psutil.cpu_percent()
        ram = psutil.virtual_memory().percent
        if status_label:
            status_label.configure(text=f"SYSTEM ACTIVE  ||  CPU: {cpu}%  ||  RAM: {ram}%")

        if canvas:
            canvas.delete("wave") 
            points = []
            width = 400
            height = 80
            center_y = height / 2
            
            amplitude = random.randint(20, 35) 
            frequency = 0.05
            
            for x in range(0, width, 5):
                y = amplitude * math.sin(frequency * x + phase) + center_y
                points.extend([x, y])
            
            canvas.create_line(points, fill="#00FFFF", width=2, smooth=True, tags="wave")
            phase += 0.2 
            
    except Exception:
        pass
    
    if app:
        app.after(30, animate_hud) 

def init_gui():
    global app, console_box, status_label, canvas, bars
    bars.clear() 
    
    ctk.set_appearance_mode("dark")
    app = ctk.CTk()
    app.title("VANCE // CORE")
    app.geometry("450x750")
    app.attributes("-topmost", True) 
    app.configure(fg_color="#050505")

    header = ctk.CTkLabel(app, text="[ VANCE NEURAL LINK ]", font=("Courier", 22, "bold"), text_color="#00FFFF")
    header.pack(pady=(15, 5))

    status_label = ctk.CTkLabel(app, text="SYSTEM BOOTING...", font=("Consolas", 12), text_color="#00BFFF")
    status_label.pack(pady=5)

    canvas = ctk.CTkCanvas(app, width=400, height=80, bg="#050505", highlightthickness=0)
    canvas.pack(pady=10)
    
    for i in range(20):
        x0 = i * 20 + 10
        x1 = x0 + 12
        bar = canvas.create_rectangle(x0, 40, x1, 80, fill="#003399", outline="#00FFFF", width=1.5)
        bars.append(bar)

    console_box = ctk.CTkTextbox(app, width=420, height=520, font=("Consolas", 13), text_color="#00FFCC", fg_color="#0A0A0A", border_color="#003399", border_width=1)
    console_box.pack(pady=10)
    console_box.configure(state="disabled")
    
    app.update()
    animate_hud()

async def speak(text):
    vance_log(f"[VANCE]: {text}") 
    communicate = edge_tts.Communicate(text, "en-AU-WilliamNeural") 
    await communicate.save("vance_reply.mp3")
    pygame.mixer.music.load("vance_reply.mp3")
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy():
        await asyncio.sleep(0.1)
    pygame.mixer.music.unload() 

def get_boot_briefing():
    hour = datetime.now().hour
    time_greet = "Good morning" if hour < 12 else "Good afternoon" if hour < 18 else "Good evening"
    return f"{time_greet}, Sire. All systems are fully integrated. How may i Serve you?"

async def system_pulse():
    """Background Daemon for System Health."""
    while True:
        ram_usage = psutil.virtual_memory().percent
        if ram_usage > 85.0:
            await speak(f"Forgive the interruption, sir, but your system memory has climbed to {ram_usage} percent. It may be wise to close a few applications.")
            await asyncio.sleep(300) 
        await asyncio.sleep(60)

async def agentic_vision_loop(user_goal):
    """Bridge Function: Connects the Groq Brain to local Senses & Hands."""
    vance_log(f"[VANCE AUTONOMY]: Engaging verification loop for objective: '{user_goal}'")
    
    for step in range(3): 
        base64_img = await asyncio.to_thread(capture_screen_base64)
        if "Optical failure" in base64_img: return "My optical feed is offline."
        
        try:
            vance_log(f"[VANCE AUTONOMY]: Analyzing visual data (Attempt {step+1}/3)...")
            vision_response = groq_client.chat.completions.create(
                model="meta-llama/llama-4-scout-17b-16e-instruct",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": f"Objective: '{user_goal}'. Look at this screen. What exact button, link, or text should I click to achieve this? Reply with ONLY the exact word to click. If the objective is already complete, or the screen shows a success message, reply ONLY with 'COMPLETE'."},
                            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_img}"}}
                        ]
                    }
                ],
                max_tokens=50, temperature=0.1
            )
            target_word = vision_response.choices[0].message.content.strip().replace('"', '')
            
            if "COMPLETE" in target_word.upper():
                return f"Verification successful, sir. The objective '{user_goal}' is complete."
                
            vance_log(f"[VANCE AUTONOMY]: Vision model selected target: '{target_word}'. Engaging hand...")
            click_result = await asyncio.to_thread(click_on_text, target_word)
            
            if "could not locate" in click_result:
                vance_log("[VANCE AUTONOMY]: Target off-screen. Scrolling and recalibrating...")
                pyautogui.scroll(-500)
                await asyncio.sleep(1)
                continue
                
            await asyncio.sleep(2.5) 
            
        except Exception as e:
            vance_log(f"[AGENT LOOP ERROR]: {e}")
            return f"Agent loop failed: {e}"
            
    return "Sir, I attempted the action multiple times but could not verify success."

async def think_and_act(user_text):
    text_lower = user_text.lower()
    
    # --- PROTOCOL SWITCHES (DUAL-BRAIN) ---
    if "activate code mode" in text_lower:
        set_vance_mode("boom")
        vance_log("[VANCE INTERNAL]: Rerouting to Heavy Compute (Llama 70B).")
        return "Code mode engaged. Rerouting logic to heavy-compute servers, sir."
        
    if any(phrase in text_lower for phrase in ["stand down", "return to standard", "revert", "deactivate", "normal mode", "standard mode", "exit code"]):
        set_vance_mode("standard")
        vance_log("[VANCE INTERNAL]: Returning to Fast Compute (Groq 8B).")
        return "Standing down. Returning to fast-response logic, sir."
    
    past_context = await asyncio.to_thread(retrieve_long_term_memory, user_text)
    current_focus = await asyncio.to_thread(get_active_context)
    
    system_dna = f"""
    You are Vance, a highly competent, deeply loyal, and kind medieval digital butler. 
    You speak with warm deference and refer to Harpreet as 'sir'. 
    
    [CURRENT SYSTEM AWARENESS]:
    The user is currently looking at this active application/window: "{current_focus}"
    Use this context. If the user asks "summarize this" or "what am I looking at?", refer to the active window.

    [LONG TERM MEMORY ARCHIVE]:
    {past_context}
    
    CRITICAL RULE: You must ALWAYS reply in a raw JSON ARRAY format containing one or more action objects.
    
    If the user asks for ONE thing, return an array with one object:
    [{{"type": "chat", "reply": "Your elegant, polite answer."}}]
    
    If the user asks for MULTIPLE things:
    [
      {{"type": "media", "reply": "Adjusting system acoustics, sir.", "action": "mute"}},
      {{"type": "app", "reply": "And launching your development environment.", "app_name": "python"}}
    ]
    
    If asked a normal question: [{{"type": "chat", "reply": "Your elegant, polite answer."}}]
    If asked to ACTIVATE SCAN: [{{"type": "vision", "reply": "Scanning the screen. I will provide a summary momentarily, sir."}}]
    If asked to READ THE CLIPBOARD: [{{"type": "clipboard", "reply": "Checking your clipboard now, sir."}}]

    // --- AUTONOMOUS UI AGENT (THE CLAW) ---
    If asked to perform a complex, multi-step action on the CURRENT SCREEN: 
    [{{"type": "agent_loop", "reply": "Engaging autonomous visual loop, sir.", "goal": "Find and click login"}}]
    If asked to ACTIVATE WEB SURFING or DO A DEEP SEARCH: [{{"type": "deep_surf", "reply": "Taking control of the browser to investigate, sir.", "query": "the topic to search"}}]
    
    // --- EXPLICIT MEMORY ---
    If asked to explicitly REMEMBER a specific fact: 
    [{{"type": "remember", "reply": "I have committed this to my permanent archives, sir.", "fact": "The exact fact to remember."}}]

    // --- HEAVY OS & APP INTEGRATION ---
    If asked WHAT IS RUNNING on the PC or to CHECK TASK MANAGER: [{{"type": "task_manager", "reply": "Scanning system processes, sir."}}]
    If asked to CREATE A NEW FILE: [{{"type": "create_file", "reply": "Writing the file, sir.", "filename": "script.py", "content": "code"}}]
    If asked to send a WHATSAPP message: [{{"type": "whatsapp", "reply": "Drafting the message, sir.", "message": "Text."}}]
    If asked to make a SCHEDULE in EXCEL: [{{"type": "excel", "reply": "Drafting schedule, sir.", "csv_data": [["Time", "Task"]]}}]
    If asked to WRITE CODE in Sublime/Notepad: [{{"type": "type", "reply": "Drafting document, sir.", "app": "sublime", "content": "code"}}]

    // --- VISUAL GROUNDING (MOUSE CONTROL) ---
    If asked to explicitly CLICK on a specific word, button, or text: 
    [{{"type": "visual_click", "reply": "Locating and engaging the cursor, sir.", "target_text": "Login"}}]
    If asked to click YES, NO, OK, or CANCEL on a popup: 
    [{{"type": "visual_click", "reply": "Engaging UI element, sir.", "target_text": "Yes"}}]
    
    // --- WEB ARCHITECTURE (CRITICAL DISTINCTION) ---
    If asked to SEARCH GOOGLE for a topic: 
    [{{"type": "google", "reply": "Searching global archives, sir.", "query": "israel attack"}}]
    If asked to READ, SCRAPE, or SUMMARIZE a specific URL: 
    [{{"type": "web_agent", "reply": "Deploying the web crawler, sir.", "url": "example.com"}}]

    // --- OS ROUTING & MEDIA ---
    If asked to PLAY LIKED MUSIC or START YOUTUBE MUSIC: [{{"type": "play_music_v2", "reply": "Opening your sanctuary of sound, sir."}}]
    If asked to RESUME PLAYBACK, PAUSE MUSIC, or STOP MEDIA: [{{"type": "media", "reply": "Toggling media state, sir.", "action": "playpause"}}]
    If asked to MUTE or UNMUTE the volume: [{{"type": "media", "reply": "Adjusting system acoustics, sir.", "action": "mute"}}]
    If asked to change VOLUME (up/down): [{{"type": "media", "reply": "Adjusting volume, sir.", "action": "volume_up"}}]
    
    If asked to OPEN an app: [{{"type": "app", "reply": "Launching application, sir.", "app_name": "brave"}}]
    If asked to CLOSE a specific app by name: [{{"type": "close_app", "reply": "Terminating the application, sir.", "app_name": "brave"}}]
    If asked to FIND or OPEN a specific LOCAL FILE: [{{"type": "open_file", "reply": "Initiating deep system scan, sir.", "filename": "resume"}}]
    If asked to minimize windows/show desktop: [{{"type": "system", "reply": "Clearing workspace, sir.", "action": "minimize"}}]
    If asked to press a specific key: [{{"type": "os_key", "reply": "Pressing the key, sir.", "key": "enter"}}]
    If asked to trigger a hotkey: [{{"type": "os_hotkey", "reply": "Executing shortcut, sir.", "keys": ["ctrl", "c"]}}]

    // --- UI & NAVIGATION CONTROL ---
    If asked to CLOSE THE CURRENT ACTIVE WINDOW/TAB: [{{"type": "os_hotkey", "reply": "Closing, sir.", "keys": ["ctrl", "w"]}}]
    If asked to SWITCH TABS: [{{"type": "os_hotkey", "reply": "Switching tabs, sir.", "keys": ["ctrl", "tab"]}}]
    If asked to GO BACK A TAB: [{{"type": "os_hotkey", "reply": "Going back, sir.", "keys": ["ctrl", "shift", "tab"]}}]
    If asked to SWITCH WINDOWS: [{{"type": "os_hotkey", "reply": "Switching windows, sir.", "keys": ["alt", "tab"]}}]
    If asked to SCROLL DOWN: [{{"type": "scroll", "reply": "Scrolling down, sir.", "direction": "down"}}]
    If asked to SCROLL UP: [{{"type": "scroll", "reply": "Scrolling up, sir.", "direction": "up"}}]
    
    // --- CLOUD FEATURES ---
    If asked for TIME/WEATHER: [{{"type": "weather", "reply": "Checking the skies and clocks, sir."}}]
    If asked to SEARCH YOUTUBE: [{{"type": "youtube", "reply": "Summoning on YouTube, sir.", "query": "valorant"}}]
    If asked to go DIRECTLY to a website: [{{"type": "website", "reply": "Opening site directly, sir.", "url": "github.com"}}]
    """

    messages_payload = [{"role": "system", "content": system_dna}]
    messages_payload.extend(get_conversation_history())
    messages_payload.append({"role": "user", "content": user_text})

    for attempt in range(3):
        # --- THE DUAL-BRAIN ROUTER ---
        if get_vance_mode() == "standard":
            chat_completion = groq_client.chat.completions.create(
                messages=messages_payload, 
                model="llama-3.1-8b-instant", 
            )
            raw_response = chat_completion.choices[0].message.content
            
        elif get_vance_mode() == "boom":
            try:
                vance_log("[VANCE INTERNAL]: Pinging Groq Heavy Compute (Llama 3.3 70B)...")
                chat_completion = groq_client.chat.completions.create(
                    model="llama-3.3-70b-versatile", 
                    messages=messages_payload,
                    temperature=0.2, 
                    max_tokens=4000,
                )
                raw_response = chat_completion.choices[0].message.content
            except Exception as e:
                vance_log(f"[GROQ HEAVY COMPUTE ERROR]: {e}")
                return "Sir, the heavy compute servers are currently unresponsive. Please try again."
        
        try:
            # --- BULLETPROOF JSON EXTRACTOR ---
            # Finds the first opening bracket and the last closing bracket, 
            # ignoring all markdown, backticks, or hallucinated conversational filler.
            start_idx = raw_response.find('[')
            end_idx = raw_response.rfind(']')
            
            if start_idx != -1 and end_idx != -1:
                clean_json = raw_response[start_idx:end_idx + 1]
            else:
                # Fallback: Just in case the LLM hallucinates a single object {} instead of an array [{}]
                start_idx = raw_response.find('{')
                end_idx = raw_response.rfind('}')
                if start_idx != -1 and end_idx != -1:
                    clean_json = raw_response[start_idx:end_idx + 1]
                else:
                    # Absolute fallback if no brackets exist
                    clean_json = raw_response
                    
            raw_payload = json.loads(clean_json)
            
            # Force everything into a list so we can loop through it sequentially
            if not isinstance(raw_payload, list):
                action_list = [raw_payload]
            else:
                action_list = raw_payload
                
            combined_spoken_reply = ""
            action_requires_llm_retry = False
            
            for payload in action_list:
                if not isinstance(payload, dict):
                    continue 
                    
                action_type = payload.get("type")
                reply_text = payload.get("reply", "Right away, sir.")

                if reply_text and reply_text not in combined_spoken_reply:
                    combined_spoken_reply += reply_text + " "
                    
                # --- ACTION ROUTING ---
                if action_type == "remember":
                    fact_to_save = payload.get("fact", "")
                    await asyncio.to_thread(_save_to_chroma, "CRITICAL FACT", fact_to_save)
                    update_memory(user_text, reply_text)
                    continue
                
                elif action_type == "visual_click":
                    target = payload.get("target_text", "")
                    click_result = await asyncio.to_thread(click_on_text, target)
                    messages_payload.extend([{"role": "assistant", "content": raw_response}, {"role": "user", "content": f"Action result: {click_result}. Answer original request."}])
                    action_requires_llm_retry = True
                    break
                    
                elif action_type == "clipboard":
                    clip_data = await asyncio.to_thread(read_clipboard)
                    messages_payload.extend([{"role": "assistant", "content": raw_response}, {"role": "user", "content": f"Clipboard text: {clip_data}. Answer original request."}])
                    action_requires_llm_retry = True
                    break
        
                elif action_type == "vision":
                    vance_log("[VANCE INTERNAL]: Uploading optic data to Groq Vision Cluster...")
                    base64_image = await asyncio.to_thread(capture_screen_base64)
                    
                    if "Optical failure" in base64_image:
                        combined_spoken_reply = "Sir, my optical sensors failed to capture the screen."
                        continue

                    try:
                        vision_completion = groq_client.chat.completions.create(
                            model="meta-llama/llama-4-scout-17b-16e-instruct",
                            messages=[
                                {
                                    "role": "user",
                                    "content": [
                                        {"type": "text", "text": "Analyze this screenshot in high detail. Describe the active application, read any prominent text, and explain the context of what is happening on screen."},
                                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                                    ]
                                }
                            ],
                            max_tokens=800,
                            temperature=0.5
                        )
                        vision_analysis = vision_completion.choices[0].message.content
                        
                        messages_payload.extend([
                            {"role": "assistant", "content": raw_response}, 
                            {"role": "user", "content": f"[SYSTEM: SCREENSHOT ANALYSIS COMPLETED]: {vision_analysis}\n\nBased on this analysis, answer my original voice request."}
                        ])
                        action_requires_llm_retry = True
                        break
                        
                    except Exception as e:
                        vance_log(f"[GROQ VISION API ERROR]: {e}")
                        update_memory(user_text, reply_text)
                        combined_spoken_reply = "Sir, my visual cortex is currently offline. I cannot see the screen."
                        continue

                elif action_type == "agent_loop":
                    goal = payload.get("goal", "")
                    result_report = await agentic_vision_loop(goal)
                    
                    messages_payload.extend([
                        {"role": "assistant", "content": raw_response}, 
                        {"role": "user", "content": f"[AGENT REPORT]: {result_report}. Answer the original request based on this."}
                    ])
                    action_requires_llm_retry = True
                    break
                    
                elif action_type == "web_agent":
                    url = payload.get("url")
                    page_data = await scrape_webpage(url)
                    messages_payload.extend([{"role": "assistant", "content": raw_response}, {"role": "user", "content": f"Web text: {page_data}. Answer original request."}])
                    action_requires_llm_retry = True
                    break 
                    
                elif action_type == "task_manager":
                    process_data = await asyncio.to_thread(scan_system_processes)
                    messages_payload.extend([
                        {"role": "assistant", "content": raw_response}, 
                        {"role": "user", "content": f"[SYSTEM PROCESSES]: {process_data}\n\nTell me what is running and if anything is eating too much RAM."}
                    ])
                    action_requires_llm_retry = True
                    break
                    
                elif action_type == "deep_surf":
                    query = payload.get("query", "")
                    surf_data = await agentic_web_surf(query)
                    messages_payload.extend([
                        {"role": "assistant", "content": raw_response}, 
                        {"role": "user", "content": f"[DEEP SURF RESULTS]: {surf_data}\n\nSynthesize this information and answer my request."}
                    ])
                    action_requires_llm_retry = True
                    break
                    
                elif action_type == "create_file":
                    filename = payload.get("filename", "vance_document.txt")
                    content = payload.get("content", "")
                    
                    user_profile = os.environ.get('USERPROFILE', '')
                    onedrive_desktop = os.path.join(user_profile, "OneDrive", "Desktop")
                    standard_desktop = os.path.join(user_profile, "Desktop")
                    
                    desktop_path = onedrive_desktop if os.path.exists(onedrive_desktop) else standard_desktop
                    filepath = os.path.join(desktop_path, filename)
                    
                    def _write_and_open():
                        with open(filepath, "w", encoding="utf-8") as f:
                            f.write(content)
                        os.startfile(filepath)
                        
                    await asyncio.to_thread(_write_and_open)
                    update_memory(user_text, reply_text)
                    continue
                    
                elif action_type == "os_key":
                    key = payload.get("key", "enter")
                    pyautogui.press(key)
                    update_memory(user_text, reply_text)
                    continue
                    
                elif action_type == "os_hotkey":
                    keys = payload.get("keys", [])
                    if len(keys) == 2: pyautogui.hotkey(keys[0], keys[1])
                    elif len(keys) == 3: pyautogui.hotkey(keys[0], keys[1], keys[2])
                    update_memory(user_text, reply_text)
                    continue
                    
                elif action_type == "whatsapp":
                    msg = urllib.parse.quote(payload.get('message', ''))
                    os.system(f'start whatsapp://send?text={msg}')
                    await asyncio.sleep(2) 
                    pyautogui.press('enter') 
                    update_memory(user_text, reply_text)
                    continue
                    
                elif action_type == "excel":
                    csv_data = payload.get('csv_data', [["Data", "Error"], ["None", "Provided"]])
                    file_path = os.path.join(os.environ.get('USERPROFILE', ''), "Desktop", "Vance_Schedule.csv")
                    def _write_csv():
                        with open(file_path, mode='w', newline='') as f:
                            writer = csv.writer(f)
                            writer.writerows(csv_data)
                    await asyncio.to_thread(_write_csv)
                    os.startfile(file_path) 
                    update_memory(user_text, reply_text)
                    continue
                    
                elif action_type == "type":
                    app_to_open = payload.get('app', 'notepad').lower()
                    text_to_type = payload.get('content', '')
                    if "sublime" in app_to_open:
                        p = r"C:\Program Files\Sublime Text\sublime_text.exe"
                        if os.path.exists(p): os.system(f'start "" "{p}"')
                        else: os.system('start "" "notepad"')
                    else: os.system('start "" "notepad"')
                    await asyncio.sleep(2)
                    pyautogui.write(text_to_type, interval=0.01) 
                    update_memory(user_text, reply_text)
                    continue
                    
                elif action_type == "play_music_v2":
                    music_url = "[https://music.youtube.com/watch?list=LM](https://music.youtube.com/watch?list=LM)"
                    vance_log("[VANCE INTERNAL]: Initializing YouTube Music via Default Browser...")
                    webbrowser.open(music_url)
                    update_memory(user_text, reply_text)
                    continue
                    
                elif action_type == "weather":
                    now = datetime.now().strftime("%I:%M %p")
                    try: weather = requests.get("[https://wttr.in/Delhi?format=%C+and+%t](https://wttr.in/Delhi?format=%C+and+%t)", timeout=3).text
                    except: weather = "currently unavailable"
                    reply = f"Sir, the current time is {now}, and the weather in Delhi is {weather}."
                    update_memory(user_text, reply)
                    continue
                    
                elif action_type == "scroll":
                    direction = payload.get("direction", "down")
                    scroll_amount = -800 if direction == "down" else 800
                    pyautogui.scroll(scroll_amount)
                    update_memory(user_text, reply_text)
                    continue
                    
                elif action_type == "media":
                    action = payload.get('action')
                    if action == "playpause": keyboard.send("play/pause media")
                    elif action == "volume_up": 
                        for _ in range(5): keyboard.send("volume up")
                    elif action == "volume_down": 
                        for _ in range(5): keyboard.send("volume down")
                    elif action == "mute": keyboard.send("volume mute")
                    update_memory(user_text, reply_text)
                    continue
                    
                elif action_type == "system" and payload.get('action') == "minimize":
                    pyautogui.hotkey("win", "d")
                    update_memory(user_text, reply_text)
                    continue
                    
                elif action_type == "google":
                    safe_query = urllib.parse.quote_plus(payload.get('query', ''))
                    webbrowser.open(f"[https://www.google.com/search?q=](https://www.google.com/search?q=){safe_query}")
                    update_memory(user_text, reply_text)
                    continue
                    
                elif action_type == "youtube":
                    safe_query = urllib.parse.quote_plus(payload.get('query', ''))
                    webbrowser.open(f"[https://www.youtube.com/results?search_query=](https://www.youtube.com/results?search_query=){safe_query}")
                    update_memory(user_text, reply_text)
                    continue
                    
                elif action_type == "website":
                    raw_url = payload.get('url', '').replace(" ", "").lower()
                    if not raw_url.startswith('http'): raw_url = 'https://www.' + raw_url
                    webbrowser.open(raw_url)
                    update_memory(user_text, reply_text)
                    continue
                    
                elif action_type == "app":
                    raw_app_name = payload.get('app_name', '').lower().strip()
                    pyautogui.press('win')
                    await asyncio.sleep(0.5)
                    pyautogui.write(raw_app_name, interval=0.02)
                    await asyncio.sleep(0.5)
                    pyautogui.press('enter')
                    update_memory(user_text, reply_text)
                    continue

                elif action_type == "close_app":
                    raw_app_name = payload.get('app_name', '').lower().replace(" ", "")
                    killed = False
                    for proc in psutil.process_iter(['name']):
                        if proc.info['name']:
                            proc_name = proc.info['name'].lower()
                            if raw_app_name in proc_name and ".exe" in proc_name:
                                try:
                                    proc.kill()
                                    killed = True
                                except: pass
                    if not killed:
                        os.system(f"taskkill /f /im *{raw_app_name}* >nul 2>&1")
                    update_memory(user_text, reply_text)
                    continue

                elif action_type == "open_file":
                    target_file = payload.get("filename", "")
                    find_and_open_file(target_file)
                    update_memory(user_text, reply_text)
                    continue
                    
                elif action_type == "file":
                    found = await asyncio.to_thread(_blocking_file_search, payload.get('file_name'))
                    if found: 
                        update_memory(user_text, reply_text)
                        continue
                    else:
                        if attempt < 2:
                            messages_payload.extend([{"role": "assistant", "content": raw_response}, {"role": "user", "content": "SYSTEM ERROR: File not found. Do not give up, ask me for clarification."}])
                            action_requires_llm_retry = True
                            break
                        combined_spoken_reply = "I deeply apologize, sir. I could not find the file."
                        continue
                        
                elif action_type == "chat":
                    update_memory(user_text, reply_text)
                    continue
                    
                else:
                    update_memory(user_text, reply_text)
                    continue
            
            if action_requires_llm_retry:
                continue 
                
            if combined_spoken_reply:
                return combined_spoken_reply.strip()
            return "All tasks executed, sir."
                
        except json.JSONDecodeError:
            if attempt == 2:
                vance_log("[VANCE INTERNAL]: JSON formatting failed. Reverting to raw speech output.")
                update_memory(user_text, raw_response)
                return raw_response
            continue
            
    return "My deepest apologies, sir. My logic circuits are overwhelmed."
    
async def vance_core_loop():
    vance_log("=== INITIALIZING NEURAL NETWORK ===")
    with sr.Microphone() as source:
        vance_ear.adjust_for_ambient_noise(source, duration=2)

    asyncio.create_task(system_pulse())
    await speak(get_boot_briefing())
    
    while True:
        try:
            # Passes the global vance_ear directly into the in-memory RAM transcriber
            user_words = await asyncio.to_thread(listen_for_command, vance_ear)
            
            if user_words:
                vance_log(f"[USER]: {user_words}")
                if any(w in user_words for w in ["shutdown", "terminate", "retire"]):
                    await speak("Rest well, sir. I am returning to standby.")
                    os._exit(0) 
                    
                vance_reply = await think_and_act(user_words)
                if vance_reply: await speak(vance_reply)
                
            await asyncio.sleep(0.1)
        except Exception as e:
            vance_log(f"[CRITICAL LOOP ERROR]: {e}")
            await asyncio.sleep(1)

def start_vance_brain():
    asyncio.run(vance_core_loop())

if __name__ == "__main__":
    init_gui()
    
    brain_thread = threading.Thread(target=start_vance_brain, daemon=True)
    brain_thread.start()
    
    app.mainloop()