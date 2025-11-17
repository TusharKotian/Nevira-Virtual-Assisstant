"""
Automation Agent - Provides unique and useful automation capabilities
"""
import os
import shutil
import json
import logging
import hashlib
import secrets
import string
import subprocess
import platform
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict

# Lazy imports for potentially slow modules
try:
    import pyperclip
    PYPERCLIP_AVAILABLE = True
except ImportError:
    PYPERCLIP_AVAILABLE = False

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

# File paths for storing automation data
AUTOMATION_DATA_DIR = os.path.join(os.path.expanduser("~"), ".nevira_automation")
TASKS_FILE = os.path.join(AUTOMATION_DATA_DIR, "tasks.json")
REMINDERS_FILE = os.path.join(AUTOMATION_DATA_DIR, "reminders.json")

# Ensure data directory exists
os.makedirs(AUTOMATION_DATA_DIR, exist_ok=True)


def _load_json_file(filepath: str, default: any = None) -> any:
    """Load JSON file, return default if doesn't exist."""
    try:
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        logging.error(f"Error loading {filepath}: {e}")
    return default if default is not None else {}


def _save_json_file(filepath: str, data: any):
    """Save data to JSON file."""
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        logging.error(f"Error saving {filepath}: {e}")


# ==================== TASK MANAGEMENT ====================

def add_task(task_description: str, priority: str = "medium", due_date: Optional[str] = None) -> str:
    """Add a new task to the task list."""
    try:
        tasks = _load_json_file(TASKS_FILE, [])
        task_id = f"task_{len(tasks) + 1}_{int(datetime.now().timestamp())}"
        new_task = {
            "id": task_id,
            "description": task_description,
            "priority": priority.lower(),
            "due_date": due_date,
            "created": datetime.now().isoformat(),
            "completed": False
        }
        tasks.append(new_task)
        _save_json_file(TASKS_FILE, tasks)
        return f"Task added successfully: '{task_description}' (Priority: {priority})"
    except Exception as e:
        return f"Error adding task: {str(e)}"


def list_tasks(show_completed: bool = False) -> str:
    """List all tasks, optionally including completed ones."""
    try:
        tasks = _load_json_file(TASKS_FILE, [])
        if not tasks:
            return "No tasks found. You're all caught up!"
        
        filtered_tasks = [t for t in tasks if show_completed or not t.get("completed", False)]
        if not filtered_tasks:
            return "No active tasks found. All tasks are completed!"
        
        result = ["📋 Your Tasks:"]
        for i, task in enumerate(filtered_tasks, 1):
            status = "✓" if task.get("completed") else "○"
            priority = task.get("priority", "medium").upper()
            due = f" (Due: {task.get('due_date')})" if task.get("due_date") else ""
            result.append(f"{i}. {status} [{priority}] {task['description']}{due}")
        
        return "\n".join(result)
    except Exception as e:
        return f"Error listing tasks: {str(e)}"


def complete_task(task_id: Optional[int] = None, task_description: Optional[str] = None) -> str:
    """Mark a task as completed."""
    try:
        tasks = _load_json_file(TASKS_FILE, [])
        if not tasks:
            return "No tasks found."
        
        # Find task by ID or description
        task = None
        if task_id:
            if 1 <= task_id <= len(tasks):
                task = tasks[task_id - 1]
        elif task_description:
            for t in tasks:
                if task_description.lower() in t["description"].lower() and not t.get("completed"):
                    task = t
                    break
        
        if not task:
            return f"Task not found."
        
        task["completed"] = True
        task["completed_at"] = datetime.now().isoformat()
        _save_json_file(TASKS_FILE, tasks)
        return f"Task marked as completed: '{task['description']}'"
    except Exception as e:
        return f"Error completing task: {str(e)}"


def delete_task(task_id: int) -> str:
    """Delete a task from the list."""
    try:
        tasks = _load_json_file(TASKS_FILE, [])
        if not tasks:
            return "No tasks found."
        
        if 1 <= task_id <= len(tasks):
            removed = tasks.pop(task_id - 1)
            _save_json_file(TASKS_FILE, tasks)
            return f"Task deleted: '{removed['description']}'"
        return f"Task ID {task_id} not found."
    except Exception as e:
        return f"Error deleting task: {str(e)}"


# ==================== FILE ORGANIZATION ====================

def organize_downloads_folder() -> str:
    """Organize files in Downloads folder by file type."""
    try:
        downloads_path = os.path.join(os.path.expanduser("~"), "Downloads")
        if not os.path.exists(downloads_path):
            return "Downloads folder not found."
        
        # File type categories
        categories = {
            "Images": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".svg", ".webp", ".ico"],
            "Documents": [".pdf", ".doc", ".docx", ".txt", ".rtf", ".xls", ".xlsx", ".ppt", ".pptx", ".odt"],
            "Videos": [".mp4", ".avi", ".mkv", ".mov", ".wmv", ".flv", ".webm"],
            "Audio": [".mp3", ".wav", ".flac", ".aac", ".ogg", ".m4a"],
            "Archives": [".zip", ".rar", ".7z", ".tar", ".gz", ".bz2"],
            "Executables": [".exe", ".msi", ".dmg", ".pkg", ".deb", ".rpm"],
            "Code": [".py", ".js", ".html", ".css", ".java", ".cpp", ".c", ".json", ".xml"]
        }
        
        moved_count = 0
        for filename in os.listdir(downloads_path):
            file_path = os.path.join(downloads_path, filename)
            if os.path.isfile(file_path):
                ext = os.path.splitext(filename)[1].lower()
                category = "Other"
                
                for cat, extensions in categories.items():
                    if ext in extensions:
                        category = cat
                        break
                
                category_folder = os.path.join(downloads_path, category)
                os.makedirs(category_folder, exist_ok=True)
                
                dest_path = os.path.join(category_folder, filename)
                if not os.path.exists(dest_path):
                    shutil.move(file_path, dest_path)
                    moved_count += 1
        
        return f"Organized Downloads folder: {moved_count} files moved into categories."
    except Exception as e:
        return f"Error organizing downloads: {str(e)}"


def find_duplicate_files(directory: str = None) -> str:
    """Find duplicate files in a directory based on file hash."""
    try:
        if not directory:
            directory = os.path.join(os.path.expanduser("~"), "Downloads")
        
        if not os.path.exists(directory):
            return f"Directory not found: {directory}"
        
        file_hashes = {}
        duplicates = []
        
        for root, dirs, files in os.walk(directory):
            for file in files:
                file_path = os.path.join(root, file)
                try:
                    # Calculate MD5 hash
                    hash_md5 = hashlib.md5()
                    with open(file_path, "rb") as f:
                        for chunk in iter(lambda: f.read(4096), b""):
                            hash_md5.update(chunk)
                    file_hash = hash_md5.hexdigest()
                    
                    if file_hash in file_hashes:
                        duplicates.append((file_path, file_hashes[file_hash]))
                    else:
                        file_hashes[file_hash] = file_path
                except Exception:
                    continue
        
        if not duplicates:
            return "No duplicate files found!"
        
        result = [f"Found {len(duplicates)} duplicate file pairs:"]
        for i, (dup, original) in enumerate(duplicates[:10], 1):
            result.append(f"{i}. {os.path.basename(dup)} (duplicate of {os.path.basename(original)})")
        
        return "\n".join(result)
    except Exception as e:
        return f"Error finding duplicates: {str(e)}"


def clean_temp_files() -> str:
    """Clean temporary files to free up disk space."""
    try:
        cleaned = 0
        total_size = 0
        
        # Cross-platform temp folder (limited scope)
        temp_dir = os.path.join(os.path.expanduser("~"), ".temp")
        if os.path.exists(temp_dir):
            for filename in os.listdir(temp_dir):
                file_path = os.path.join(temp_dir, filename)
                try:
                    if os.path.isfile(file_path):
                        size = os.path.getsize(file_path)
                        os.remove(file_path)
                        cleaned += 1
                        total_size += size
                except Exception:
                    pass
        
        # Clean Python cache in current project directory only (much faster)
        current_dir = os.getcwd()
        if os.path.exists(current_dir):
            # Limit search to current project and immediate subdirectories
            for root, dirs, files in os.walk(current_dir):
                # Limit depth to prevent long searches
                depth = root[len(current_dir):].count(os.sep)
                if depth > 3:  # Only search 3 levels deep
                    dirs[:] = []  # Don't recurse deeper
                    continue
                    
                if "__pycache__" in dirs:
                    cache_dir = os.path.join(root, "__pycache__")
                    try:
                        size = sum(os.path.getsize(os.path.join(cache_dir, f)) 
                                 for f in os.listdir(cache_dir) 
                                 if os.path.isfile(os.path.join(cache_dir, f)))
                        shutil.rmtree(cache_dir)
                        cleaned += 1
                        total_size += size
                    except Exception:
                        pass
        
        size_mb = total_size / (1024 * 1024) if total_size > 0 else 0
        return f"Cleaned {cleaned} temporary files, freed {size_mb:.2f} MB."
    except Exception as e:
        return f"Error cleaning temp files: {str(e)}"


# ==================== CLIPBOARD OPERATIONS ====================

def get_clipboard() -> str:
    """Get current clipboard content."""
    if not PYPERCLIP_AVAILABLE:
        return "Clipboard not available. Please install pyperclip: pip install pyperclip"
    try:
        clipboard_text = pyperclip.paste()
        if not clipboard_text:
            return "Clipboard is empty."
        # Limit length for display
        if len(clipboard_text) > 200:
            return f"Clipboard content (first 200 chars): {clipboard_text[:200]}..."
        return f"Clipboard content: {clipboard_text}"
    except Exception as e:
        return f"Error reading clipboard: {str(e)}"


def set_clipboard(text: str) -> str:
    """Set clipboard content."""
    if not PYPERCLIP_AVAILABLE:
        return "Clipboard not available. Please install pyperclip: pip install pyperclip"
    try:
        pyperclip.copy(text)
        # Limit length for display
        display_text = text[:50] + "..." if len(text) > 50 else text
        return f"Copied to clipboard: {display_text}"
    except Exception as e:
        return f"Error setting clipboard: {str(e)}"


# ==================== PASSWORD GENERATOR ====================

def generate_secure_password(length: int = 16, include_symbols: bool = True) -> str:
    """Generate a secure random password."""
    try:
        characters = string.ascii_letters + string.digits
        if include_symbols:
            characters += "!@#$%^&*()_+-=[]{}|;:,.<>?"
        
        password = ''.join(secrets.choice(characters) for _ in range(length))
        
        # Copy to clipboard automatically if available
        if PYPERCLIP_AVAILABLE:
            try:
                pyperclip.copy(password)
                return f"Generated password (copied to clipboard): {password}"
            except Exception:
                return f"Generated password: {password}"
        else:
            return f"Generated password: {password}"
    except Exception as e:
        return f"Error generating password: {str(e)}"


# ==================== TEXT MANIPULATION ====================

def word_count(text: str) -> str:
    """Count words, characters, and lines in text."""
    try:
        words = len(text.split())
        chars = len(text)
        chars_no_spaces = len(text.replace(" ", ""))
        lines = len(text.splitlines())
        sentences = len([s for s in text.split('.') if s.strip()])
        
        return f"Text Analysis:\n- Words: {words}\n- Characters: {chars} (without spaces: {chars_no_spaces})\n- Lines: {lines}\n- Sentences: {sentences}"
    except Exception as e:
        return f"Error counting words: {str(e)}"


# ==================== NETWORK MONITORING ====================

def check_internet_connection() -> str:
    """Check internet connectivity and speed."""
    if not REQUESTS_AVAILABLE:
        return "requests not available. Please install: pip install requests"
    try:
        # Check connectivity
        response = requests.get("https://www.google.com", timeout=5)
        if response.status_code == 200:
            # Simple speed test (ping time)
            import time
            start = time.time()
            requests.get("https://www.google.com", timeout=5)
            latency = (time.time() - start) * 1000
            
            return f"Internet connection: ✓ Active\nPing to Google: {latency:.2f}ms"
    except Exception:
        pass
    
    return "Internet connection: ✗ Not available"


def get_network_stats() -> str:
    """Get network statistics."""
    if not PSUTIL_AVAILABLE:
        return "psutil not available. Please install: pip install psutil"
    try:
        net_io = psutil.net_io_counters()
        stats = {
            "Bytes sent": f"{net_io.bytes_sent / (1024**2):.2f} MB",
            "Bytes received": f"{net_io.bytes_recv / (1024**2):.2f} MB",
            "Packets sent": net_io.packets_sent,
            "Packets received": net_io.packets_recv
        }
        
        result = ["Network Statistics:"]
        for key, value in stats.items():
            result.append(f"- {key}: {value}")
        
        return "\n".join(result)
    except Exception as e:
        return f"Error getting network stats: {str(e)}"


# ==================== PROCESS MANAGEMENT ====================

def list_running_processes(top_n: int = 10) -> str:
    """List top processes by CPU usage."""
    if not PSUTIL_AVAILABLE:
        return "psutil not available. Please install: pip install psutil"
    try:
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
            try:
                proc_info = proc.info
                if proc_info['cpu_percent'] is not None:
                    processes.append(proc_info)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        
        # Sort by CPU usage
        processes.sort(key=lambda x: x['cpu_percent'] or 0, reverse=True)
        
        result = [f"Top {top_n} processes by CPU usage:"]
        for i, proc in enumerate(processes[:top_n], 1):
            name = proc['name'] or 'Unknown'
            cpu = proc['cpu_percent'] or 0
            mem = proc['memory_percent'] or 0
            result.append(f"{i}. {name} - CPU: {cpu:.1f}%, Memory: {mem:.1f}%")
        
        return "\n".join(result)
    except Exception as e:
        return f"Error listing processes: {str(e)}"


def kill_process_by_name(process_name: str) -> str:
    """Kill a process by name."""
    if not PSUTIL_AVAILABLE:
        return "psutil not available. Please install: pip install psutil"
    try:
        killed = 0
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                if process_name.lower() in proc.info['name'].lower():
                    proc.kill()
                    killed += 1
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        
        if killed > 0:
            return f"Killed {killed} process(es) matching '{process_name}'"
        return f"No processes found matching '{process_name}'"
    except Exception as e:
        return f"Error killing process: {str(e)}"


# ==================== SYSTEM MAINTENANCE ====================

def get_disk_usage(path: str = None) -> str:
    """Get disk usage statistics."""
    try:
        if not path:
            path = os.path.expanduser("~")
        
        usage = shutil.disk_usage(path)
        total_gb = usage.total / (1024**3)
        used_gb = usage.used / (1024**3)
        free_gb = usage.free / (1024**3)
        used_percent = (used_gb / total_gb) * 100
        
        result = f"Disk Usage for {path}:\n"
        result += f"- Total: {total_gb:.2f} GB\n"
        result += f"- Used: {used_gb:.2f} GB ({used_percent:.1f}%)\n"
        result += f"- Free: {free_gb:.2f} GB"
        
        if used_percent > 90:
            result += "\n⚠️ Warning: Disk space is running low!"
        
        return result
    except Exception as e:
        return f"Error getting disk usage: {str(e)}"

