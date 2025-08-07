#!/usr/bin/env python3
"""
Real-time Resource Monitor for Dolores System
Shows CPU, memory, database activity, and rate limiting status
"""

import time
import os
import psutil
from resource_manager import get_resource_manager
from pathlib import Path

def clear_screen():
    """Clear terminal screen"""
    os.system('clear' if os.name == 'posix' else 'cls')

def format_bytes(bytes_value):
    """Format bytes to human readable format"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_value < 1024.0:
            return f"{bytes_value:.1f} {unit}"
        bytes_value /= 1024.0
    return f"{bytes_value:.1f} TB"

def get_dolores_memory_info():
    """Get Dolores memory database info"""
    try:
        db_path = Path("./dolores_knowledge/dolores_memory.db")
        if db_path.exists():
            size = db_path.stat().st_size
            return format_bytes(size)
        return "Not found"
    except Exception:
        return "Error"

def display_system_stats():
    """Display comprehensive system statistics"""
    rm = get_resource_manager()
    stats = rm.get_stats()
    
    # System info
    cpu_percent = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    
    # Process info
    current_process = psutil.Process()
    process_memory = current_process.memory_info()
    
    clear_screen()
    print("=" * 80)
    print(" 🤖 DOLORES SYSTEM RESOURCE MONITOR")
    print("=" * 80)
    
    # System Resources
    print(f"\n📊 SYSTEM RESOURCES")
    print(f"   CPU Usage:     {cpu_percent:6.1f}% {'⚠️ HIGH' if cpu_percent > 75 else '✅'}")
    print(f"   Memory:        {memory.percent:6.1f}% ({format_bytes(memory.used)} / {format_bytes(memory.total)})")
    print(f"   Available:     {format_bytes(memory.available)}")
    print(f"   Disk Usage:    {disk.percent:6.1f}% ({format_bytes(disk.used)} / {format_bytes(disk.total)})")
    
    # Process Resources
    print(f"\n🔧 DOLORES PROCESS")
    print(f"   Process Memory: {format_bytes(process_memory.rss)}")
    print(f"   Virtual Memory: {format_bytes(process_memory.vms)}")
    print(f"   CPU Time:      {current_process.cpu_times().user:.1f}s user, {current_process.cpu_times().system:.1f}s system")
    print(f"   Uptime:        {stats['uptime_seconds']:.0f} seconds")
    
    # Database Info
    print(f"\n💾 DATABASE STATUS")
    print(f"   Active Connections: {stats['active_db_connections']}")
    print(f"   Database Size:     {get_dolores_memory_info()}")
    print(f"   Memory Available:  {stats['memory_available_gb']:.2f} GB")
    
    # Rate Limiting
    print(f"\n⏱️  RATE LIMITING")
    print(f"   API Tokens:    {stats['api_tokens_available']:6.1f} / 5")
    print(f"   DB Tokens:     {stats['db_tokens_available']:6.1f} / 10")
    api_status = "🟢 READY" if stats['api_tokens_available'] > 1 else "🔴 THROTTLED"
    db_status = "🟢 READY" if stats['db_tokens_available'] > 1 else "🔴 THROTTLED"
    print(f"   API Status:    {api_status}")
    print(f"   DB Status:     {db_status}")
    
    # Operation Counts
    print(f"\n📈 OPERATION STATISTICS")
    total_ops = sum(stats['operation_counts'].values())
    print(f"   Total Operations:  {total_ops}")
    for op_type, count in stats['operation_counts'].items():
        print(f"   {op_type.title():15}: {count}")
    
    # Performance Indicators
    print(f"\n🎯 PERFORMANCE INDICATORS")
    if cpu_percent > 80:
        print("   ⚠️  High CPU usage - operations may be throttled")
    if memory.percent > 85:
        print("   ⚠️  High memory usage - consider restarting")
    if stats['active_db_connections'] >= 3:
        print("   ⚠️  Database connection limit reached")
    if stats['api_tokens_available'] < 1:
        print("   ⚠️  API rate limit active - responses may be delayed")
    
    if cpu_percent < 50 and memory.percent < 70 and stats['api_tokens_available'] > 2:
        print("   ✅ System running optimally")
    
    print(f"\nPress Ctrl+C to exit | Refreshing every 5 seconds...")
    print("=" * 80)

def monitor_loop():
    """Main monitoring loop"""
    try:
        while True:
            display_system_stats()
            time.sleep(5)
    except KeyboardInterrupt:
        clear_screen()
        print("Resource monitor stopped.")

def quick_status():
    """Display quick status summary"""
    rm = get_resource_manager()
    stats = rm.get_stats()
    cpu_percent = psutil.cpu_percent()
    memory = psutil.virtual_memory()
    
    print(f"Quick Status: CPU {cpu_percent:.1f}%, Memory {memory.percent:.1f}%, "
          f"Operations {sum(stats['operation_counts'].values())}, "
          f"API tokens {stats['api_tokens_available']:.1f}")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "quick":
        quick_status()
    else:
        print("Starting Dolores Resource Monitor...")
        print("This will show real-time system resource usage.")
        print("Press Ctrl+C to exit.\n")
        time.sleep(2)
        monitor_loop()