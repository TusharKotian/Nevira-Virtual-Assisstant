# Testing Automation Agent Features

## Quick Test Script

Run the automated test script:

```bash
python test_automation.py
```

This will test all automation features and show you the results.

## Manual Testing with Voice Agent

### Start the Agent

1. **Development mode (with LiveKit Dashboard):**
   ```bash
   python agent.py dev
   ```

2. **Or if you have a UI running:**
   ```bash
   # Make sure your token server is running
   cd token-server
   npm start
   
   # Then start the agent in another terminal
   python agent.py
   ```

### Test Commands to Say

#### Task Management
- "Add a task to review code"
- "Add a high priority task to finish project by Friday"
- "Show me my tasks"
- "List all tasks"
- "Complete task 1"
- "Mark task review code as completed"
- "Delete task 2"

#### Clipboard Operations
- "What's in my clipboard?"
- "Copy this text to clipboard: Hello World"
- "Set clipboard to my email address"

#### Password Generator
- "Generate a password"
- "Generate a 20 character password"
- "Generate a 12 character password without symbols"

#### Text Utilities
- "Count words in this text: The quick brown fox jumps over the lazy dog"
- "Word count: This is a test sentence with multiple words"

#### Network Monitoring
- "Check my internet connection"
- "Is the internet working?"
- "Show network statistics"
- "Get network stats"

#### System Management
- "Show me disk usage"
- "Check disk space"
- "List top processes"
- "List top 5 processes by CPU"
- "Show running processes"

#### File Organization
- "Organize my Downloads folder"
- "Organize downloads"
- "Find duplicate files"
- "Find duplicates in my Downloads folder"
- "Clean temporary files"
- "Clean temp files"

## Testing Individual Functions (Python Console)

You can also test functions directly in Python:

```python
# Start Python
python

# Import and test
from automation_agent import add_task, list_tasks, generate_secure_password

# Test adding a task
add_task("Test task", "high")
list_tasks()

# Test password generation
generate_secure_password(16, True)
```

## Expected Behavior

### Task Management
- Tasks are saved in `~/.nevira_automation/tasks.json`
- Tasks persist between sessions
- Can mark tasks complete or delete them

### Clipboard
- Can read and write clipboard content
- Useful for copying generated passwords automatically

### Password Generator
- Generates cryptographically secure passwords
- Automatically copies to clipboard
- Configurable length and symbol inclusion

### File Organization
- Organizes Downloads folder by file type
- Creates folders: Images, Documents, Videos, Audio, Archives, Executables, Code

### System Functions
- Shows real-time disk usage
- Lists processes by CPU usage
- Cleans temp files and Python cache

## Troubleshooting

### If clipboard doesn't work:
```bash
pip install pyperclip
```

### If a function fails:
- Check the error message in the console
- Make sure you have necessary permissions (e.g., file access)
- Some functions require admin privileges (like killing processes)

### Check if automation agent is loaded:
- Look for "Nevira assistant started and ready" in logs
- The agent should list all tools including automation ones

## Example Conversation Flow

**You:** "Add a task to finish project documentation"

**Nevira:** "Task added successfully: 'finish project documentation' (Priority: medium)"

**You:** "Show me my tasks"

**Nevira:** "📋 Your Tasks:
1. ○ [MEDIUM] finish project documentation
..."

**You:** "Generate a secure password"

**Nevira:** "Generated password (copied to clipboard): aB3$kL9#mN2@pQ7&"

**You:** "Organize my Downloads folder"

**Nevira:** "Organized Downloads folder: 15 files moved into categories."

