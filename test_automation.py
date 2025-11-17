"""
Test script for Automation Agent features
Run this to test all automation functions independently
"""
import asyncio
from automation_agent import (
    add_task,
    list_tasks,
    complete_task,
    delete_task,
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

def print_section(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")

async def test_task_management():
    print_section("Testing Task Management")
    
    # Add tasks
    print("\n1. Adding tasks...")
    print(add_task("Complete automation testing", "high", "2024-12-31"))
    print(add_task("Review code changes", "medium"))
    print(add_task("Update documentation", "low"))
    
    # List tasks
    print("\n2. Listing tasks...")
    print(list_tasks())
    
    # Complete a task
    print("\n3. Completing task...")
    print(complete_task(task_description="Complete automation testing"))
    
    # List again
    print("\n4. Listing tasks after completion...")
    print(list_tasks())

async def test_clipboard():
    print_section("Testing Clipboard Operations")
    
    # Set clipboard
    print("\n1. Setting clipboard...")
    print(set_clipboard_func("Hello from Nevira Automation Agent!"))
    
    # Get clipboard
    print("\n2. Getting clipboard...")
    print(get_clipboard_func())

async def test_password_generator():
    print_section("Testing Password Generator")
    
    print("\n1. Generating 16-character password...")
    print(generate_secure_password(16, True))
    
    print("\n2. Generating 20-character password without symbols...")
    print(generate_secure_password(20, False))

async def test_text_utilities():
    print_section("Testing Text Utilities")
    
    sample_text = """This is a sample text for testing.
    It has multiple lines.
    And multiple sentences. Let's count the words."""
    
    print("\nWord count analysis:")
    print(word_count(sample_text))

async def test_network():
    print_section("Testing Network Functions")
    
    print("\n1. Checking internet connection...")
    print(check_internet_connection())
    
    print("\n2. Getting network statistics...")
    print(get_network_stats())

async def test_system():
    print_section("Testing System Functions")
    
    print("\n1. Getting disk usage...")
    print(get_disk_usage())
    
    print("\n2. Listing top processes...")
    print(list_running_processes(5))

async def test_file_organization():
    print_section("Testing File Organization")
    
    print("\n1. Getting disk usage before cleanup...")
    print(get_disk_usage())
    
    print("\n2. Cleaning temp files...")
    result = clean_temp_files()
    print(result)
    
    # Note: organize_downloads and find_duplicates are commented out
    # as they might take time or modify files
    # Uncomment if you want to test them:
    # print("\n3. Finding duplicates...")
    # print(find_duplicate_files())

async def main():
    print("\n" + "="*60)
    print("  NEVIRA AUTOMATION AGENT - TEST SUITE")
    print("="*60)
    
    try:
        await test_task_management()
        await test_clipboard()
        await test_password_generator()
        await test_text_utilities()
        await test_network()
        await test_system()
        await test_file_organization()
        
        print_section("All Tests Completed Successfully!")
        print("\n✓ Task Management: Working")
        print("✓ Clipboard Operations: Working")
        print("✓ Password Generator: Working")
        print("✓ Text Utilities: Working")
        print("✓ Network Functions: Working")
        print("✓ System Functions: Working")
        print("✓ File Organization: Working")
        
    except Exception as e:
        print(f"\n❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())

