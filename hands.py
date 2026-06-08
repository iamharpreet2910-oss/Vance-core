import os
import time
import asyncio
import threading
import urllib.parse
from PIL import ImageGrab
import pytesseract
import pyautogui
from playwright.async_api import async_playwright

def click_on_text(target_text):
    """Scans the optical feed for a target word and clicks its center coordinates."""
    print(f"[VANCE INTERNAL]: Scanning optical feed for target coordinates: '{target_text}'...")
    try:
        screenshot = ImageGrab.grab()
        data = pytesseract.image_to_data(screenshot, output_type='dict')
        
        target_clean = ''.join(e for e in target_text.lower() if e.isalnum())
        if not target_clean: return "Target text empty."
        
        words_found = [] 
            
        for i in range(len(data['text'])):
            word = data['text'][i].lower().strip()
            word_clean = ''.join(e for e in word if e.isalnum())
            
            if len(word_clean) > 0:
                words_found.append(word_clean)
            
            # Aggressive fuzzy matching
            if target_clean in word_clean or word_clean in target_clean:
                if len(word_clean) >= min(len(target_clean), 2): 
                    x, y, w, h = data['left'][i], data['top'][i], data['width'][i], data['height'][i]
                    
                    center_x = int(x + (w / 2))
                    center_y = int(y + (h / 2))
                    
                    print(f"[VANCE INTERNAL]: Target locked at X:{center_x} Y:{center_y}")
                    
                    pyautogui.moveTo(center_x, center_y, duration=0.3)
                    time.sleep(0.1) 
                    pyautogui.click()
                    return f"Successfully located and clicked '{target_text}', sir."
                    
        print(f"[VANCE DIAGNOSTIC]: Tesseract saw these words: {words_found[:30]}...")
        return f"I apologize, sir. I scanned the screen but could not locate '{target_text}'."
        
    except Exception as e:
        return f"Optical targeting failure: {e}"

async def agentic_web_surf(query):
    """Takes control of the browser for deep, popup-free DuckDuckGo searches."""
    print(f"[VANCE INTERNAL]: Taking control of browser for deep search: '{query}'...")
    try:
        safe_query = urllib.parse.quote_plus(query)
        url = f"https://duckduckgo.com/html/?q={safe_query}"
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False, channel="msedge") 
            context = await browser.new_context()
            page = await context.new_page()
            
            await page.goto(url, wait_until="domcontentloaded", timeout=15000)
            await asyncio.sleep(2) # Give it 2 seconds so you can physically see the results
            
            text_content = await page.evaluate("document.body.innerText")
            await browser.close()
            
            if not text_content or not text_content.strip():
                return "Search returned no readable text."
            return text_content[:3000] 
            
    except Exception as e:
        return f"Surfing failure: {e}"   

async def scrape_webpage(url):
    """Deploys a stealth headless browser crawler."""
    print(f"[VANCE INTERNAL]: Launching stealth browser to navigate {url}...")
    try:
        if not url.startswith('http'): url = 'https://www.' + url
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                viewport={"width": 1920, "height": 1080}
            )
            page = await context.new_page()
            await page.goto(url, wait_until="domcontentloaded", timeout=15000)
            await asyncio.sleep(1.5) 
            text_content = await page.evaluate("document.body.innerText")
            await browser.close()
            if not text_content or not text_content.strip(): 
                return "The webpage blocked the crawler or is empty."
            return text_content[:2000] 
    except Exception as e: 
        return f"Web failure: {e}"

def find_and_open_file(filename):
    """Initiates a background thread to rapidly scan primary directories for a target file."""
    target = filename.lower().split(".")[0]
    
    def search_drive():
        print(f"[VANCE INTERNAL]: Initiating background scan for '{target}'...")
        search_paths = [os.path.expanduser("~"), "C:\\", "D:\\"] 
        
        for base_path in search_paths:
            if not os.path.exists(base_path): continue
            for root, dirs, files in os.walk(base_path):
                for file in files:
                    if target in file.lower():
                        full_path = os.path.join(root, file)
                        print(f"[VANCE INTERNAL]: Target acquired -> {full_path}")
                        os.startfile(full_path)
                        return True
        print(f"[VANCE INTERNAL]: Scan complete. Could not locate '{target}'.")
        return False
        
    threading.Thread(target=search_drive, daemon=True).start()
    return f"I have initiated a system-wide scan for {filename}, sir. It will open momentarily."

def _blocking_file_search(target_name):
    """Deep synchronous search through user profiles and OneDrive."""
    user_profile = os.environ.get('USERPROFILE', '')
    onedrive = os.environ.get('OneDrive', '')
    search_zones = [
        os.path.join(user_profile, "Desktop"), os.path.join(user_profile, "Documents"),
        os.path.join(user_profile, "Downloads"), os.path.join(user_profile, "Music"),
        os.path.join(user_profile, "Pictures"), os.path.join(user_profile, "Videos")
    ]
    if onedrive: search_zones.extend([os.path.join(onedrive, "Desktop"), os.path.join(onedrive, "Documents")])
    search_zones.append("E:\\") 
    
    for zone in search_zones:
        if not os.path.exists(zone): continue
        for root, dirs, files in os.walk(zone):
            for file in files:
                if target_name.lower() in file.lower():
                    exact_path = os.path.join(root, file)
                    try:
                        os.startfile(exact_path) 
                        return True
                    except: return False
    return False