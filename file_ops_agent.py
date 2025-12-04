"""
FileOpsAgent - Advanced file operations for Nevira assistant
Provides safe, intelligent file management capabilities
"""
import os
import json
import logging
import shutil
import hashlib
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Tuple, Any
from dataclasses import dataclass

# Lazy imports for optional dependencies
try:
    import send2trash  # type: ignore
    SEND2TRASH_AVAILABLE = True
except ImportError:
    SEND2TRASH_AVAILABLE = False

# Configuration
LOG_DIR = Path.home() / ".nevira_fileops"
LOG_FILE = LOG_DIR / "operations.json"
UNDO_FILE = LOG_DIR / "undo_stack.json"

# Ensure directories exist
LOG_DIR.mkdir(exist_ok=True)

@dataclass
class FileInfo:
    """Structured file information"""
    name: str
    path: str
    size: int
    size_mb: float
    type: str
    modified: str
    is_dir: bool

def _log_operation(operation: str, details: Dict[str, Any]) -> None:
    """Log file operations for auditing and undo functionality"""
    try:
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "operation": operation,
            "details": details
        }

        # Load existing logs
        logs = []
        if LOG_FILE.exists():
            try:
                with open(LOG_FILE, 'r', encoding='utf-8') as f:
                    logs = json.load(f)
            except:
                logs = []

        logs.append(log_entry)

        # Keep only last 1000 operations
        if len(logs) > 1000:
            logs = logs[-1000:]

        with open(LOG_FILE, 'w', encoding='utf-8') as f:
            json.dump(logs, f, indent=2, ensure_ascii=False)

    except Exception as e:
        logging.error(f"Failed to log operation: {e}")

def _get_file_info(path: Path) -> FileInfo:
    """Get structured file information"""
    try:
        stat = path.stat()
        size_mb = stat.st_size / (1024 * 1024)
        modified = datetime.fromtimestamp(stat.st_mtime).isoformat()

        # Determine file type
        if path.is_dir():
            file_type = "directory"
        else:
            suffix = path.suffix.lower()
            type_map = {
                '.txt': 'text', '.md': 'markdown', '.py': 'python', '.js': 'javascript',
                '.html': 'html', '.css': 'css', '.json': 'json', '.xml': 'xml',
                '.pdf': 'pdf', '.doc': 'document', '.docx': 'document',
                '.jpg': 'image', '.jpeg': 'image', '.png': 'image', '.gif': 'image',
                '.mp4': 'video', '.avi': 'video', '.mp3': 'audio', '.wav': 'audio',
                '.zip': 'archive', '.rar': 'archive', '.7z': 'archive'
            }
            file_type = type_map.get(suffix, 'file')

        return FileInfo(
            name=path.name,
            path=str(path),
            size=stat.st_size,
            size_mb=round(size_mb, 2),
            type=file_type,
            modified=modified,
            is_dir=path.is_dir()
        )
    except Exception:
        return FileInfo(
            name=path.name,
            path=str(path),
            size=0,
            size_mb=0,
            type="unknown",
            modified="unknown",
            is_dir=path.is_dir()
        )

def list_files(
    directory: str,
    extension: Optional[str] = None,
    name_contains: Optional[str] = None,
    size_min_mb: Optional[float] = None,
    size_max_mb: Optional[float] = None,
    modified_days: Optional[int] = None,
    limit: int = 50
) -> str:
    """List files in directory with optional filters"""
    try:
        path = Path(directory).expanduser().resolve()
        if not path.exists() or not path.is_dir():
            return f"Directory not found: {directory}"

        files = []
        for item in path.rglob("*"):
            if item.is_file():
                info = _get_file_info(item)

                # Apply filters
                if extension and not item.suffix.lower() == f".{extension.lower()}":
                    continue
                if name_contains and name_contains.lower() not in item.name.lower():
                    continue
                if size_min_mb and info.size_mb < size_min_mb:
                    continue
                if size_max_mb and info.size_mb > size_max_mb:
                    continue
                if modified_days:
                    modified_time = datetime.fromisoformat(info.modified.replace('Z', '+00:00'))
                    if datetime.now(modified_time.tzinfo) - modified_time > timedelta(days=modified_days):
                        continue

                files.append(info)

        # Sort by modified time (newest first)
        files.sort(key=lambda x: x.modified, reverse=True)

        # Limit results
        files = files[:limit]

        if not files:
            return f"No files found in {directory} matching criteria."

        result = [f"Files in {directory} ({len(files)} found):"]
        for i, f in enumerate(files, 1):
            result.append(f"{i}. {f.name} ({f.size_mb:.1f}MB, {f.type}, {f.modified[:10]})")

        return "\n".join(result)

    except Exception as e:
        return f"Error listing files: {str(e)}"

def rename_files(
    directory: str,
    prefix: Optional[str] = None,
    suffix: Optional[str] = None,
    replace_old: Optional[str] = None,
    replace_new: Optional[str] = None,
    add_sequence: bool = False,
    confirm: bool = False
) -> str:
    """Rename files with specified rules"""
    try:
        path = Path(directory).expanduser().resolve()
        if not path.exists() or not path.is_dir():
            return f"Directory not found: {directory}"

        files = [f for f in path.iterdir() if f.is_file()]
        if not files:
            return f"No files found in {directory}"

        # Generate preview
        preview = []
        operations = []

        for i, file_path in enumerate(files):
            old_name = file_path.name
            stem = file_path.stem
            ext = file_path.suffix

            new_stem = stem
            if prefix:
                new_stem = prefix + new_stem
            if suffix:
                new_stem = new_stem + suffix
            if replace_old and replace_new:
                new_stem = new_stem.replace(replace_old, replace_new)
            if add_sequence:
                new_stem = f"{new_stem}_{i+1:03d}"

            new_name = new_stem + ext
            new_path = file_path.parent / new_name

            if new_name != old_name:
                preview.append(f"'{old_name}' → '{new_name}'")
                operations.append((file_path, new_path))

        if not operations:
            return "No files need renaming with current rules."

        if not confirm:
            preview_text = "\n".join(preview[:10])
            if len(preview) > 10:
                preview_text += f"\n... and {len(preview)-10} more"
            return f"Dry run - {len(operations)} files to rename:\n{preview_text}\n\nAdd confirm=True to execute."

        # Execute renames
        renamed = 0
        for old_path, new_path in operations:
            try:
                old_path.rename(new_path)
                renamed += 1
            except Exception as e:
                logging.error(f"Failed to rename {old_path}: {e}")

        # Log operation
        _log_operation("rename_files", {
            "directory": str(path),
            "rules": {"prefix": prefix, "suffix": suffix, "replace": f"{replace_old}->{replace_new}", "sequence": add_sequence},
            "files_renamed": renamed,
            "total_files": len(operations)
        })

        return f"Renamed {renamed} files in {directory}"

    except Exception as e:
        return f"Error renaming files: {str(e)}"

def move_files(
    source_dir: str,
    dest_dir: str,
    extension: Optional[str] = None,
    name_contains: Optional[str] = None,
    confirm: bool = False
) -> str:
    """Move files based on conditions"""
    try:
        source = Path(source_dir).expanduser().resolve()
        dest = Path(dest_dir).expanduser().resolve()

        if not source.exists() or not source.is_dir():
            return f"Source directory not found: {source_dir}"
        if not dest.exists():
            dest.mkdir(parents=True, exist_ok=True)

        files = [f for f in source.iterdir() if f.is_file()]

        # Apply filters
        to_move = []
        for f in files:
            if extension and f.suffix.lower() != f".{extension.lower()}":
                continue
            if name_contains and name_contains.lower() not in f.name.lower():
                continue
            to_move.append(f)

        if not to_move:
            return "No files match the move criteria."

        if not confirm:
            file_list = [f.name for f in to_move[:10]]
            if len(to_move) > 10:
                file_list.append(f"... and {len(to_move)-10} more")
            return f"Dry run - {len(to_move)} files to move from {source_dir} to {dest_dir}:\n" + "\n".join(file_list) + "\n\nAdd confirm=True to execute."

        # Execute moves
        moved = 0
        for file_path in to_move:
            try:
                shutil.move(str(file_path), str(dest))
                moved += 1
            except Exception as e:
                logging.error(f"Failed to move {file_path}: {e}")

        # Log operation
        _log_operation("move_files", {
            "source": str(source),
            "destination": str(dest),
            "filters": {"extension": extension, "name_contains": name_contains},
            "files_moved": moved
        })

        return f"Moved {moved} files from {source_dir} to {dest_dir}"

    except Exception as e:
        return f"Error moving files: {str(e)}"

def organize_folder(directory: str, confirm: bool = False) -> str:
    """Organize folder by file type"""
    try:
        path = Path(directory).expanduser().resolve()
        if not path.exists() or not path.is_dir():
            return f"Directory not found: {directory}"

        # File type categories
        categories = {
            "Images": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".svg", ".webp"],
            "Documents": [".pdf", ".doc", ".docx", ".txt", ".rtf", ".xls", ".xlsx", ".ppt", ".pptx"],
            "Videos": [".mp4", ".avi", ".mkv", ".mov", ".wmv", ".flv"],
            "Audio": [".mp3", ".wav", ".flac", ".aac", ".ogg"],
            "Archives": [".zip", ".rar", ".7z", ".tar", ".gz"],
            "Code": [".py", ".js", ".html", ".css", ".java", ".cpp", ".c", ".json", ".xml"],
            "Executables": [".exe", ".msi", ".dmg", ".pkg"]
        }

        operations = []
        for file_path in path.iterdir():
            if file_path.is_file():
                ext = file_path.suffix.lower()
                category = "Other"

                for cat, extensions in categories.items():
                    if ext in extensions:
                        category = cat
                        break

                category_dir = path / category
                if not category_dir.exists():
                    operations.append(("create_dir", category_dir))

                dest_path = category_dir / file_path.name
                if file_path != dest_path:
                    operations.append(("move", file_path, dest_path))

        if not operations:
            return "Folder is already organized."

        if not confirm:
            create_dirs = [str(op[1]) for op in operations if op[0] == "create_dir"]
            moves = [(str(op[1]), str(op[2])) for op in operations if op[0] == "move"]
            return f"Dry run - Organization plan:\nCreate {len(create_dirs)} folders: {', '.join(create_dirs)}\nMove {len(moves)} files\n\nAdd confirm=True to execute."

        # Execute
        created = 0
        moved = 0
        for op in operations:
            if op[0] == "create_dir":
                op[1].mkdir(exist_ok=True)
                created += 1
            elif op[0] == "move":
                try:
                    shutil.move(str(op[1]), str(op[2]))
                    moved += 1
                except Exception as e:
                    logging.error(f"Failed to move {op[1]}: {e}")

        # Log operation
        _log_operation("organize_folder", {
            "directory": str(path),
            "folders_created": created,
            "files_moved": moved
        })

        return f"Organized {directory}: created {created} folders, moved {moved} files."

    except Exception as e:
        return f"Error organizing folder: {str(e)}"

def analyze_file(filepath: str) -> str:
    """Analyze file content for text files"""
    try:
        path = Path(filepath).expanduser().resolve()
        if not path.exists() or not path.is_file():
            return f"File not found: {filepath}"

        ext = path.suffix.lower()
        text_extensions = ['.txt', '.md', '.py', '.js', '.html', '.css', '.json', '.xml', '.log']

        if ext not in text_extensions:
            info = _get_file_info(path)
            return f"File: {info.name}\nSize: {info.size_mb:.1f}MB\nType: {info.type}\nModified: {info.modified}\n\nContent analysis not available for this file type."

        try:
            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
        except:
            return "Unable to read file content (may be binary or encoded differently)."

        # Basic analysis
        lines = content.splitlines()
        words = content.split()
        chars = len(content)

        # Find TODO/FIXME
        todos = []
        for i, line in enumerate(lines, 1):
            line_lower = line.lower()
            if 'todo' in line_lower or 'fixme' in line_lower or 'hack' in line_lower:
                todos.append(f"Line {i}: {line.strip()}")

        # Find errors (basic)
        errors = []
        for i, line in enumerate(lines, 1):
            if any(word in line.lower() for word in ['error', 'exception', 'failed', 'traceback']):
                errors.append(f"Line {i}: {line.strip()}")

        result = f"File Analysis: {path.name}\n"
        result += f"Lines: {len(lines)}, Words: {len(words)}, Characters: {chars}\n\n"

        if todos:
            result += f"TODO/FIXME items ({len(todos)}):\n" + "\n".join(todos[:5]) + "\n\n"
        else:
            result += "No TODO/FIXME items found.\n\n"

        if errors:
            result += f"Potential errors ({len(errors)}):\n" + "\n".join(errors[:5]) + "\n\n"
        else:
            result += "No obvious errors found.\n\n"

        # Summary (first 500 chars)
        summary = content[:500].replace('\n', ' ').strip()
        if len(content) > 500:
            summary += "..."
        result += f"Content preview: {summary}"

        return result

    except Exception as e:
        return f"Error analyzing file: {str(e)}"

def find_large_files(directory: str, size_threshold_mb: float = 100) -> str:
    """Find files larger than threshold"""
    try:
        path = Path(directory).expanduser().resolve()
        if not path.exists() or not path.is_dir():
            return f"Directory not found: {directory}"

        large_files = []
        for root, dirs, files in os.walk(path):
            for file in files:
                file_path = Path(root) / file
                try:
                    size_mb = file_path.stat().st_size / (1024 * 1024)
                    if size_mb >= size_threshold_mb:
                        large_files.append((file_path, size_mb))
                except:
                    continue

        if not large_files:
            return f"No files larger than {size_threshold_mb}MB found in {directory}"

        # Sort by size descending
        large_files.sort(key=lambda x: x[1], reverse=True)

        result = [f"Large files in {directory} (>={size_threshold_mb}MB):"]
        for file_path, size_mb in large_files[:20]:
            result.append(f"- {file_path.name}: {size_mb:.1f}MB ({file_path})")

        return "\n".join(result)

    except Exception as e:
        return f"Error finding large files: {str(e)}"

def find_duplicates(directory: str) -> str:
    """Find duplicate files by content hash"""
    try:
        path = Path(directory).expanduser().resolve()
        if not path.exists() or not path.is_dir():
            return f"Directory not found: {directory}"

        file_hashes = {}
        duplicates = []

        for root, dirs, files in os.walk(path):
            for file in files:
                file_path = Path(root) / file
                try:
                    # Skip very large files
                    if file_path.stat().st_size > 100 * 1024 * 1024:  # 100MB
                        continue

                    hash_md5 = hashlib.md5()
                    with open(file_path, "rb") as f:
                        for chunk in iter(lambda: f.read(4096), b""):
                            hash_md5.update(chunk)
                    file_hash = hash_md5.hexdigest()

                    if file_hash in file_hashes:
                        duplicates.append((str(file_path), str(file_hashes[file_hash])))
                    else:
                        file_hashes[file_hash] = file_path
                except:
                    continue

        if not duplicates:
            return f"No duplicate files found in {directory}"

        result = [f"Found {len(duplicates)} duplicate file pairs in {directory}:"]
        for i, (dup, original) in enumerate(duplicates[:10], 1):
            result.append(f"{i}. {Path(dup).name} (duplicate of {Path(original).name})")

        return "\n".join(result)

    except Exception as e:
        return f"Error finding duplicates: {str(e)}"

def undo_last_operation() -> str:
    """Undo the last file operation (limited support)"""
    try:
        if not LOG_FILE.exists():
            return "No operation log found to undo."

        with open(LOG_FILE, 'r', encoding='utf-8') as f:
            logs = json.load(f)

        if not logs:
            return "No operations to undo."

        last_op = logs[-1]

        # For now, only support basic undo for moves (would need more complex logic for renames)
        if last_op["operation"] == "move_files":
            # This is complex to undo automatically, so just show what was done
            details = last_op["details"]
            return f"Last operation was a move: {details['files_moved']} files from {details['source']} to {details['destination']}. Manual undo required."

        elif last_op["operation"] == "rename_files":
            return "Rename operations cannot be automatically undone. Check the log for details."

        else:
            return f"Last operation ({last_op['operation']}) cannot be undone automatically."

    except Exception as e:
        return f"Error undoing operation: {str(e)}"

# Main interface for natural language commands
def handle_command(command: str) -> str:
    """Parse natural language command and execute appropriate action"""
    command = command.lower().strip()

    try:
        if "list" in command and "file" in command:
            # Extract directory
            if "downloads" in command:
                directory = "~/Downloads"
            elif "documents" in command:
                directory = "~/Documents"
            elif "desktop" in command:
                directory = "~/Desktop"
            else:
                directory = "~/Downloads"  # default

            # Extract filters
            extension = None
            if "pdf" in command:
                extension = "pdf"
            elif "python" in command or "py" in command:
                extension = "py"

            return list_files(directory, extension=extension)

        elif "organize" in command:
            directory = "~/Downloads"  # default
            if "confirm" in command or "do it" in command:
                return organize_folder(directory, confirm=True)
            else:
                return organize_folder(directory, confirm=False)

        elif "rename" in command:
            directory = "~/Downloads"
            if "confirm" in command:
                return rename_files(directory, add_sequence=True, confirm=True)
            else:
                return rename_files(directory, add_sequence=True, confirm=False)

        elif "large files" in command or "big files" in command:
            return find_large_files("~/Downloads", 50)

        elif "duplicate" in command:
            return find_duplicates("~/Downloads")

        elif "analyze" in command:
            # This would need file path extraction - simplified
            return "Please specify a file path to analyze."

        else:
            return "FileOpsAgent: I can help with listing files, organizing folders, renaming files, finding large files, and detecting duplicates. Try commands like 'list files in downloads' or 'organize downloads'."

    except Exception as e:
        return f"Error processing command: {str(e)}"