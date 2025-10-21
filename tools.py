import logging
import os
import re
import json
import datetime
import webbrowser
import platform
from typing import Optional
import asyncio
import requests
import pyautogui
import psutil
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from ddgs import DDGS
from livekit.agents import function_tool, RunContext

from movie_ticket_agent import book_ticket
from latest_news_agent import get_latest_news

@function_tool()
async def get_latest_news_tool(category: str = "business", count: int = 5) -> str:
    try:
        news_text = get_latest_news(category=category, count=count)
        if not news_text:
            return f"No news found in {category} category."
        return news_text
    except Exception as e:
        return f"Failed to fetch news: {str(e)}"

@function_tool()
async def book_movie_ticket_tool(movie_name: str, location: str, date: str, num_tickets: int = 1) -> str:
    try:
        result = await book_ticket(event_type="movie", location=location, date=date, num_tickets=num_tickets)
        return f"Movie booking status: {result}"
    except Exception as e:
        return f"Failed to book movie tickets: {str(e)}"

@function_tool()
async def get_weather(context: RunContext, city: str) -> str:
    try:
        response = requests.get(f"https://wttr.in/{city}?format=3")
        if response.status_code == 200:
            logging.info(f"Weather for {city}: {response.text.strip()}")
            return response.text.strip()
        else:
            logging.error(f"Failed to get weather for {city}: {response.status_code}")
            return f"Could not retrieve weather for {city}."
    except Exception as e:
        logging.error(f"Error retrieving weather for {city}: {e}")
        return f"An error occurred while retrieving weather for {city}."

@function_tool()
async def search_web(context: RunContext, query: str) -> str:
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=5))
            if not results:
                return f"No search results found for '{query}'."
            formatted_results = []
            for i, result in enumerate(results, 1):
                title = result.get('title', 'No title')
                body = result.get('body', 'No description')
                url = result.get('href', '')
                formatted_results.append(f"{i}. {title}\n   {body}\n   {url}")
            output = "\n\n".join(formatted_results)
            logging.info(f"Search results for '{query}': Found {len(results)} results")
            return output
    except Exception as e:
        logging.error(f"Error searching the web for '{query}': {e}")
        return f"An error occurred while searching the web for '{query}'."

def _looks_like_email(value: str) -> bool:
    return bool(re.fullmatch(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", value or ""))


def _load_contacts() -> dict:
    try:
        contacts_env = os.getenv("CONTACTS_JSON", "")
        if contacts_env:
            return json.loads(contacts_env)
    except Exception:
        pass
    return {}


def _resolve_email(recipient: str) -> Optional[str]:
    recipient = (recipient or "").strip()
    if not recipient:
        return None
    if _looks_like_email(recipient):
        return recipient
    contacts = _load_contacts()
    key = recipient.lower()
    if key in contacts and _looks_like_email(contacts[key]):
        return contacts[key]
    try:
        with DDGS() as ddgs:
            query = f"{recipient} email address"
            results = list(ddgs.text(query, max_results=5))
            for r in results:
                text = " ".join([
                    str(r.get("title", "")),
                    str(r.get("body", "")),
                    str(r.get("href", "")),
                ])
                matches = re.findall(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", text)
                for email in matches:
                    if _looks_like_email(email):
                        return email
    except Exception:
        pass
    return None


@function_tool()    
async def send_email(context: RunContext, to_email: str, subject: str, message: str, cc_email: Optional[str] = None) -> str:
    try:
        smtp_server = "smtp.gmail.com"
        smtp_port = 587
        gmail_user = os.getenv("GMAIL_USER")
        gmail_password = os.getenv("GMAIL_APP_PASSWORD")
        if not gmail_user or not gmail_password:
            logging.error("Gmail credentials not found in environment variables")
            return "Email sending failed: Gmail credentials not configured."
        resolved_to = _resolve_email(to_email)
        if not resolved_to:
            return f"Email sending failed: Could not resolve a valid email for '{to_email}'."
        msg = MIMEMultipart()
        msg['From'] = gmail_user
        msg['To'] = resolved_to
        msg['Subject'] = subject
        recipients = [resolved_to]
        if cc_email:
            cc_final = cc_email if _looks_like_email(cc_email) else _resolve_email(cc_email)
            if cc_final:
                msg['Cc'] = cc_final
                recipients.append(cc_final)
        msg.attach(MIMEText(message, 'plain'))
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(gmail_user, gmail_password)
        server.sendmail(gmail_user, recipients, msg.as_string())
        server.quit()
        logging.info(f"Email sent successfully to {resolved_to}")
        return f"Email sent successfully to {resolved_to}"
    except smtplib.SMTPAuthenticationError:
        logging.error("Gmail authentication failed")
        return "Email sending failed: Authentication error. Please check your Gmail credentials."
    except smtplib.SMTPException as e:
        logging.error(f"SMTP error occurred: {e}")
        return f"Email sending failed: SMTP error - {str(e)}"
    except Exception as e:
        logging.error(f"Error sending email: {e}")
        return f"An error occurred while sending email: {str(e)}"

@function_tool()
async def control_volume(context: RunContext, action: str) -> str:
    try:
        action = action.lower().strip()
        if action in ["up", "increase", "raise"]:
            pyautogui.press("volumeup")
            logging.info("Volume increased")
            return "Volume increased, Boss."
        elif action in ["down", "decrease", "lower"]:
            pyautogui.press("volumedown")
            logging.info("Volume decreased")
            return "Volume decreased, Boss."
        elif action in ["mute", "silence"]:
            pyautogui.press("volumemute")
            logging.info("Volume muted")
            return "Volume muted, Boss."
        elif action in ["unmute"]:
            pyautogui.press("volumemute")
            logging.info("Volume unmuted")
            return "Volume unmuted, Boss."
        else:
            return f"Invalid action '{action}'. Use: up, down, mute, or unmute."
    except Exception as e:
        logging.error(f"Error controlling volume: {e}")
        return f"Could not control volume: {str(e)}"

@function_tool()
async def open_application(context: RunContext, app_name: str) -> str:
    try:
        app_name = app_name.lower().strip()
        apps = {
            "calculator": "calc.exe",
            "notepad": "notepad.exe",
            "paint": "mspaint.exe",
            "cmd": "cmd.exe",
            "command prompt": "cmd.exe",
            "explorer": "explorer.exe",
            "file explorer": "explorer.exe",
            "task manager": "taskmgr.exe",
            "settings": "ms-settings:",
        }
        if app_name in apps:
            if apps[app_name].startswith("ms-"):
                webbrowser.open(apps[app_name])
            else:
                os.startfile(apps[app_name])
            logging.info(f"Opened {app_name}")
            return f"Opening {app_name} now, Boss."
        else:
            available = ", ".join(apps.keys())
            return f"I don't know how to open '{app_name}'. Available apps: {available}"
    except Exception as e:
        logging.error(f"Error opening application '{app_name}': {e}")
        return f"Could not open {app_name}: {str(e)}"

@function_tool()
async def close_application(context: RunContext, app_name: str) -> str:
    try:
        app_name = app_name.lower().strip()
        app_processes = {
            "calculator": ["Calculator.exe", "ApplicationFrameHost.exe"],
            "notepad": ["notepad.exe"],
            "paint": ["mspaint.exe"],
            "chrome": ["chrome.exe"],
            "edge": ["msedge.exe"],
        }
        if app_name not in app_processes:
            available = ", ".join(app_processes.keys())
            return f"I don't know how to close '{app_name}'. Available: {available}"
        for process_name in app_processes[app_name]:
            if platform.system() == "Windows":
                os.system(f'taskkill /f /im {process_name} 2>nul')
        logging.info(f"Closed {app_name}")
        return f"Closed {app_name}, Boss."
    except Exception as e:
        logging.error(f"Error closing application '{app_name}': {e}")
        return f"Could not close {app_name}: {str(e)}"

@function_tool()
async def open_website(context: RunContext, site_name: str) -> str:
    try:
        site_name = site_name.strip()
        site_lower = site_name.lower()
        sites = {
            'youtube': 'https://youtube.com',
            'facebook': 'https://facebook.com',
            'instagram': 'https://instagram.com',
            'whatsapp': 'https://web.whatsapp.com',
            'discord': 'https://discord.com',
            'twitter': 'https://twitter.com',
            'x': 'https://x.com',
            'github': 'https://github.com',
            'google': 'https://google.com',
            'gmail': 'https://gmail.com',
            'reddit': 'https://reddit.com',
            'linkedin': 'https://linkedin.com',
        }
        # If the command includes a YouTube play intent, open top result directly
        if site_lower.startswith('youtube '):
            query = site_name.split(' ', 1)[1]
            try:
                with DDGS() as ddgs:
                    video_results = list(ddgs.videos(keywords=query, max_results=1))
                if video_results:
                    url = video_results[0].get('content') or video_results[0].get('url') or video_results[0].get('href')
                    if url:
                        webbrowser.open(url)
                        return f"Playing top YouTube result for '{query}', Boss."
            except Exception:
                pass
            webbrowser.open(f"https://www.youtube.com/results?search_query={query.replace(' ', '+')}")
            return f"Opening YouTube search for '{query}', Boss."
        if site_lower in sites:
            webbrowser.open(sites[site_lower])
            logging.info(f"Opened {site_lower}")
            return f"Opening {site_lower}, Boss."
        else:
            if '.' in site_lower or site_lower.startswith('http'):
                url = site_name if site_lower.startswith('http') else f'https://{site_name}'
                webbrowser.open(url)
                return f"Opening {url}, Boss."
            else:
                available = ", ".join(sites.keys())
                return f"Unknown site '{site_name}'. Popular sites: {available}"
    except Exception as e:
        logging.error(f"Error opening website '{site_name}': {e}")
        return f"Could not open website: {str(e)}"

@function_tool()
async def search_google(context: RunContext, query: str) -> str:
    try:
        search_url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
        webbrowser.open(search_url)
        logging.info(f"Searching Google for: {query}")
        return f"Searching Google for '{query}', Boss."
    except Exception as e:
        logging.error(f"Error searching Google: {e}")
        return f"Could not perform Google search: {str(e)}"

@function_tool()
async def get_system_status(context: RunContext) -> str:
    try:
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        memory_percent = memory.percent
        battery = psutil.sensors_battery()
        battery_info = f"Battery: Not available (desktop system)"
        if battery:
            battery_percent = battery.percent
            plugged = "plugged in" if battery.power_plugged else "on battery"
            battery_info = f"Battery: {battery_percent}% ({plugged})"
        disk = psutil.disk_usage('/')
        disk_percent = disk.percent
        status = f"System Status:\n- CPU Usage: {cpu_percent}%\n- Memory Usage: {memory_percent}%\n- Disk Usage: {disk_percent}%\n- {battery_info}"
        logging.info(f"System status retrieved: CPU {cpu_percent}%, Memory {memory_percent}%")
        return status
    except Exception as e:
        logging.error(f"Error getting system status: {e}")
        return f"Could not retrieve system status: {str(e)}"

@function_tool()
async def get_schedule(context: RunContext, day: Optional[str] = None) -> str:
    try:
        if not day or day.lower() == "today":
            current_day = datetime.datetime.today().weekday()
            day_names = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
            day = day_names[current_day]
        else:
            day = day.lower().strip()
        schedule = {
            "monday": "From 9:00 AM to 9:50 AM you have Algorithm class, from 10:00 AM to 11:50 AM you have DSA class.",
            "tuesday": "From 9:00 AM to 9:50 AM you have Database Management class, from 10:00 AM to 11:50 AM you have Computer Networks class, from 2:00 PM to 4:50 PM you have DSA Lab.",
            "wednesday": "From 9:00 AM to 9:50 AM you have Operating Systems class, from 10:00 AM to 11:50 AM you have Software Engineering class, from 2:00 PM to 4:50 PM you have CN Lab.",
            "thursday": "From 9:00 AM to 9:50 AM you have Database Management class, from 10:00 AM to 11:50 AM you have Algorithm class, from 2:00 PM to 4:50 PM you have DBMS Lab.",
            "friday": "From 9:00 AM to 9:50 AM you have Operating Systems class, from 10:00 AM to 11:50 AM you have Computer Networks class.",
            "saturday": "From 9:00 AM to 9:50 AM you have Software Engineering class, from 10:00 AM to 11:50 AM you have Open Elective or Extra class.",
            "sunday": "You are free today, Boss. Time to relax or revise!"
        }
        if day in schedule:
            logging.info(f"Retrieved schedule for {day}")
            return f"Your schedule for {day.title()}: {schedule[day]}"
        else:
            return f"I don't have schedule information for '{day}'."
    except Exception as e:
        logging.error(f"Error getting schedule: {e}")
        return f"Could not retrieve schedule: {str(e)}"

@function_tool()
async def get_time_and_date(context: RunContext) -> str:
    try:
        now = datetime.datetime.now()
        day_name = now.strftime("%A")
        date_str = now.strftime("%B %d, %Y")
        time_str = now.strftime("%I:%M %p")
        result = f"Boss, today is {day_name}, {date_str}, and the current time is {time_str}."
        logging.info(f"Time and date retrieved: {result}")
        return result
    except Exception as e:
        logging.error(f"Error getting time and date: {e}")
        return f"Boss, I could not retrieve the time and date due to an error: {str(e)}"

@function_tool()
async def take_screenshot(context: RunContext, filename: Optional[str] = None) -> str:
    try:
        pictures_dir = os.path.join(os.path.expanduser("~"), "Pictures", "Screenshots")
        os.makedirs(pictures_dir, exist_ok=True)
        if not filename:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"screenshot_{timestamp}"
        filepath = os.path.join(pictures_dir, f"{filename}.png")
        screenshot = pyautogui.screenshot()
        screenshot.save(filepath)
        logging.info(f"Screenshot saved to {filepath}")
        return f"Screenshot saved to {filepath}, Boss."
    except Exception as e:
        logging.error(f"Error taking screenshot: {e}")
        return f"Could not take screenshot: {str(e)}"
@function_tool(name="shutdown_system", description="Shuts down the user's computer safely.")
async def shutdown_system(context: RunContext) -> str:
    """
    Shuts down the system safely.
    """
    try:
        os_name = platform.system().lower()
        if "windows" in os_name:
            await asyncio.create_subprocess_shell("shutdown /s /t 1")
        elif "linux" in os_name or "darwin" in os_name:  # macOS is Darwin
            await asyncio.create_subprocess_shell("sudo shutdown -h now")
        else:
            return "Unsupported operating system for shutdown command."
        
        return "System shutdown initiated. Please save your work."
    except Exception as e:
        return f"Error while trying to shut down: {str(e)}"


@function_tool(name="restart_system", description="Restarts the user's computer safely.")
async def restart_system(context: RunContext) -> str:
    """
    Restarts the system safely.
    """
    try:
        os_name = platform.system().lower()
        if "windows" in os_name:
            await asyncio.create_subprocess_shell("shutdown /r /t 1")
        elif "linux" in os_name or "darwin" in os_name:
            await asyncio.create_subprocess_shell("sudo shutdown -r now")
        else:
            return "Unsupported operating system for restart command."
        
        return "System restart initiated. Please save your work."
    except Exception as e:
        return f"Error while trying to restart: {str(e)}"