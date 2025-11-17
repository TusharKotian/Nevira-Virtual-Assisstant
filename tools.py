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
from automation_agent import (
    add_task as add_task_func,
    list_tasks as list_tasks_func,
    complete_task as complete_task_func,
    delete_task as delete_task_func,
    organize_downloads_folder,
    find_duplicate_files,
    clean_temp_files,
    get_clipboard as get_clipboard_func,
    set_clipboard as set_clipboard_func,
    generate_secure_password,
    word_count,
    check_internet_connection,
    get_network_stats,
    list_running_processes,
    kill_process_by_name,
    get_disk_usage
)

async def _send_to_ui(context: RunContext, text: str, images: list = None):
    """Helper function to send messages to UI chat."""
    try:
        import json
        payload = {
            "type": "assistant_message",
            "message": text,
            "text": text,
            "images": images or [],
            "timestamp": datetime.datetime.now().isoformat()
        }
        if context and context.room:
            await context.room.local_participant.publish_data(
                json.dumps(payload).encode('utf-8'),
                reliable=True
            )
    except Exception as e:
        logging.warning(f"Could not send message to UI: {e}")

@function_tool()
async def get_latest_news_tool(context: RunContext, category: str = "business", count: int = 5) -> str:
    """Get latest news with improved error handling."""
    try:
        news_text = await asyncio.to_thread(get_latest_news, category, count)
        if not news_text:
            result = f"I couldn't find any news in the {category} category, Boss. Please try again or try a different category."
        else:
            result = news_text
        # Send to UI
        await _send_to_ui(context, result)
        return result
    except Exception as e:
        logging.error(f"Error in get_latest_news_tool: {e}")
        result = f"I apologize, Boss. I encountered an issue fetching {category} news: {str(e)}. Please try again in a moment."
        await _send_to_ui(context, result)
        return result

@function_tool()
async def book_movie_ticket_tool(movie_name: str, location: str, date: str, num_tickets: int = 1) -> str:
    """Book movie tickets with improved error handling."""
    try:
        result = await asyncio.to_thread(book_ticket, "movie", location, date, num_tickets)
        # The book_ticket function already returns user-friendly messages
        return result
    except Exception as e:
        logging.error(f"Error in book_movie_ticket_tool: {e}")
        return f"I apologize, Boss. An unexpected error occurred while booking movie tickets: {str(e)}. Please try again or visit BookMyShow directly."

@function_tool()
async def get_weather(context: RunContext, city: str) -> str:
    """Get weather information for a city with improved error handling."""
    import urllib.parse
    
    # Clean and encode city name
    city_clean = city.strip()
    city_encoded = urllib.parse.quote(city_clean)
    
    # Try multiple formats for better results
    formats = [
        f"https://wttr.in/{city_encoded}?format=3",
        f"https://wttr.in/{city_encoded}?format=1",
    ]
    
    for url in formats:
        try:
            response = requests.get(url, timeout=10, headers={
                'User-Agent': 'Mozilla/5.0 (compatible; Nevira Assistant)'
            })
            
            if response.status_code == 200:
                weather_text = response.text.strip()
                if weather_text and weather_text != "Unknown location":
                    logging.info(f"Weather for {city_clean}: {weather_text}")
                    return f"Weather in {city_clean}: {weather_text}"
            
        except requests.exceptions.Timeout:
            logging.warning(f"Weather API timeout for {city_clean}")
            continue
        except requests.exceptions.RequestException as e:
            logging.warning(f"Weather API request error for {city_clean}: {e}")
            continue
        except Exception as e:
            logging.error(f"Unexpected error getting weather for {city_clean}: {e}")
            continue
    
    # Fallback message
    return f"I apologize, Boss. I couldn't retrieve the weather for {city_clean} at this moment. Please try again in a moment, or check the city name is correct."

@function_tool()
async def search_web(context: RunContext, query: str) -> str:
    """Search the web with improved error handling and retries."""
    if not query or not query.strip():
        return "Boss, I need a search query to help you. What would you like me to search for?"
    
    query_clean = query.strip()
    max_retries = 2
    
    for attempt in range(max_retries):
        try:
            with DDGS(timeout=10) as ddgs:
                results = list(ddgs.text(query_clean, max_results=5))
                
                if not results:
                    # Try with a simpler query on retry
                    if attempt < max_retries - 1:
                        continue
                    return f"I couldn't find any results for '{query_clean}', Boss. Perhaps try rephrasing your search or checking the spelling."
                
                formatted_results = []
                for i, result in enumerate(results, 1):
                    title = result.get('title', 'No title') or 'No title'
                    body = result.get('body', 'No description') or 'No description available'
                    url = result.get('href', '') or result.get('url', '')
                    
                    # Truncate long descriptions
                    if len(body) > 200:
                        body = body[:200] + "..."
                    
                    formatted_results.append(
                        f"{i}. {title}\n   {body}\n   {url if url else 'URL not available'}"
                    )
                
                output = f"I found {len(results)} result(s) for '{query_clean}':\n\n" + "\n\n".join(formatted_results)
                logging.info(f"Search results for '{query_clean}': Found {len(results)} results")
                return output
                
        except Exception as e:
            logging.error(f"Error searching the web for '{query_clean}' (attempt {attempt + 1}): {e}")
            if attempt < max_retries - 1:
                await asyncio.sleep(1)  # Wait before retry
                continue
            return f"I apologize, Boss. I encountered an issue searching for '{query_clean}'. Please try again in a moment."

def _looks_like_email(value: str) -> bool:
    return bool(re.fullmatch(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", value or ""))


def _load_contacts() -> dict:
    """
    Load contacts from environment variable or return default contacts.
    Default contacts are hardcoded for quick access.
    """
    # Default contacts
    default_contacts = {
        "tushar": "22j61.tushar@sjec.ac.in",
        "kevin": "22j25.kevin@sjec.ac.in",
        "aden": "22j01.aden@sjec.ac.in"
    }
    
    # Load from environment variable if available (will override defaults)
    try:
        contacts_env = os.getenv("CONTACTS_JSON", "")
        if contacts_env:
            env_contacts = json.loads(contacts_env)
            # Merge with defaults (env takes precedence)
            default_contacts.update(env_contacts)
            return default_contacts
    except Exception:
        pass
    
    return default_contacts


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
async def open_email_composer(context: RunContext) -> str:
    """
    Opens the email composer popup interface for the user to fill in email details.
    This is triggered when user says 'send email' without specific details.
    """
    try:
        # Send data message to trigger popup in UI
        import json
        data = {
            "type": "email_popup_trigger",
            "message": "Opening email composer for you, Boss.",
            "timestamp": datetime.datetime.now().isoformat()
        }
        
        # Send data message to trigger popup
        await context.room.local_participant.publish_data(
            json.dumps(data).encode('utf-8'), 
            reliable=True
        )
        
        logging.info("Sent email popup trigger data message")
    except Exception as e:
        logging.error(f"Error sending email popup trigger: {e}")
    
    return "Opening email composer for you, Boss."

@function_tool()    
async def send_email(context: RunContext, to_email: str, subject: str, message: str, cc_email: Optional[str] = None) -> str:
    try:
        smtp_server = "smtp.gmail.com"
        smtp_port = 587
        # Use environment variables if set, otherwise use default credentials
        gmail_user = os.getenv("GMAIL_USER") or "nevirachatbot@gmail.com"
        gmail_password = os.getenv("GMAIL_APP_PASSWORD") or "nevira123"
        
        # Note: For production, it's recommended to use an app-specific password
        # The password "nevira123" may not work if 2FA is enabled or if Google requires app passwords
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
        return "I apologize, Boss. Email authentication failed. If 2FA is enabled on your Gmail account, you'll need to use an App Password instead of your regular password. You can create one at https://myaccount.google.com/apppasswords"
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


# ==================== AUTOMATION TOOLS ====================

@function_tool()
async def add_task(context: RunContext, task_description: str, priority: str = "medium", due_date: Optional[str] = None) -> str:
    """Add a new task to your task list."""
    return await asyncio.to_thread(add_task_func, task_description, priority, due_date)


@function_tool()
async def list_tasks(context: RunContext, show_completed: bool = False) -> str:
    """List all your tasks."""
    return await asyncio.to_thread(list_tasks_func, show_completed)


@function_tool()
async def complete_task(context: RunContext, task_id: Optional[int] = None, task_description: Optional[str] = None) -> str:
    """Mark a task as completed. Provide either task_id (number) or task_description."""
    return await asyncio.to_thread(complete_task_func, task_id, task_description)


@function_tool()
async def delete_task(context: RunContext, task_id: int) -> str:
    """Delete a task by its ID number."""
    return await asyncio.to_thread(delete_task_func, task_id)


@function_tool()
async def organize_downloads(context: RunContext) -> str:
    """Organize files in Downloads folder by file type (Images, Documents, Videos, etc.)."""
    return await asyncio.to_thread(organize_downloads_folder)


@function_tool()
async def find_duplicates(context: RunContext, directory: Optional[str] = None) -> str:
    """Find duplicate files in a directory based on file content."""
    return await asyncio.to_thread(find_duplicate_files, directory)


@function_tool()
async def clean_temp(context: RunContext) -> str:
    """Clean temporary files and cache to free up disk space."""
    return await asyncio.to_thread(clean_temp_files)


@function_tool()
async def get_clipboard(context: RunContext) -> str:
    """Get the current content of the clipboard."""
    return await asyncio.to_thread(get_clipboard_func)


@function_tool()
async def set_clipboard(context: RunContext, text: str) -> str:
    """Copy text to the clipboard."""
    return await asyncio.to_thread(set_clipboard_func, text)


@function_tool()
async def generate_password(context: RunContext, length: int = 16, include_symbols: bool = True) -> str:
    """Generate a secure random password. Automatically copies to clipboard."""
    return await asyncio.to_thread(generate_secure_password, length, include_symbols)


@function_tool()
async def word_count(context: RunContext, text: str) -> str:
    """Count words, characters, lines, and sentences in text."""
    return await asyncio.to_thread(word_count, text)


@function_tool()
async def check_internet(context: RunContext) -> str:
    """Check internet connectivity and ping latency."""
    return await asyncio.to_thread(check_internet_connection)


@function_tool()
async def get_network_stats(context: RunContext) -> str:
    """Get network statistics (bytes sent/received, packets)."""
    return await asyncio.to_thread(get_network_stats)


@function_tool()
async def list_processes(context: RunContext, top_n: int = 10) -> str:
    """List top running processes by CPU usage."""
    return await asyncio.to_thread(list_running_processes, top_n)


@function_tool()
async def kill_process(context: RunContext, process_name: str) -> str:
    """Kill a running process by name."""
    return await asyncio.to_thread(kill_process_by_name, process_name)


@function_tool()
async def get_disk_usage(context: RunContext, path: Optional[str] = None) -> str:
    """Get disk usage statistics for a path (defaults to home directory)."""
    return await asyncio.to_thread(get_disk_usage, path)