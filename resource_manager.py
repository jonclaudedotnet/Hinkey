#!/usr/bin/env python3
"""
Resource Management and Throttling System for Dolores
Prevents CPU overload and manages system resources efficiently
"""

import time
import threading
import psutil
import sqlite3
from collections import defaultdict, deque
from contextlib import contextmanager
from typing import Optional, Dict, Any
import functools
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RateLimiter:
    """Token bucket rate limiter for API calls and operations"""
    
    def __init__(self, max_tokens: int = 10, refill_rate: float = 1.0):
        self.max_tokens = max_tokens
        self.tokens = max_tokens
        self.refill_rate = refill_rate
        self.last_refill = time.time()
        self.lock = threading.Lock()
    
    def acquire(self, tokens: int = 1) -> bool:
        """Try to acquire tokens. Returns True if successful."""
        with self.lock:
            now = time.time()
            # Refill tokens based on time elapsed
            elapsed = now - self.last_refill
            self.tokens = min(self.max_tokens, 
                             self.tokens + elapsed * self.refill_rate)
            self.last_refill = now
            
            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            return False
    
    def wait_for_token(self, tokens: int = 1, timeout: Optional[float] = None):
        """Wait until tokens are available"""
        start_time = time.time()
        while not self.acquire(tokens):
            if timeout and (time.time() - start_time) > timeout:
                raise TimeoutError("Rate limit timeout")
            time.sleep(0.1)

class CPUThrottler:
    """Monitor CPU usage and throttle operations when needed"""
    
    def __init__(self, cpu_threshold: float = 80.0, check_interval: float = 1.0):
        self.cpu_threshold = cpu_threshold
        self.check_interval = check_interval
        self.last_check = 0
        self.cpu_history = deque(maxlen=10)
        self.lock = threading.Lock()
    
    def should_throttle(self) -> bool:
        """Check if we should throttle based on CPU usage"""
        now = time.time()
        with self.lock:
            if now - self.last_check > self.check_interval:
                cpu_percent = psutil.cpu_percent(interval=None)
                self.cpu_history.append(cpu_percent)
                self.last_check = now
                
                # Throttle if recent average is high
                if len(self.cpu_history) >= 3:
                    avg_cpu = sum(list(self.cpu_history)[-3:]) / 3
                    return avg_cpu > self.cpu_threshold
        
        return False
    
    def throttle_if_needed(self, sleep_time: float = 0.01):
        """Sleep if CPU usage is high - MINIMAL"""
        if self.should_throttle():
            # Very brief pause only
            actual_sleep = sleep_time
            logger.info(f"CPU throttling: sleeping {actual_sleep}s")
            time.sleep(actual_sleep)

class DatabaseThrottler:
    """Manage database connections and query throttling"""
    
    def __init__(self, max_connections: int = 5, query_delay: float = 0.1):
        self.max_connections = max_connections
        self.query_delay = query_delay  # Much longer delay between queries
        self.active_connections = 0
        self.connection_lock = threading.Semaphore(max_connections)
        self.query_times = deque(maxlen=100)
        self.lock = threading.Lock()
    
    @contextmanager
    def get_connection(self, db_path: str):
        """Get a throttled database connection"""
        self.connection_lock.acquire()
        try:
            self.active_connections += 1
            conn = sqlite3.connect(db_path, timeout=30.0)
            # Enable WAL mode for better concurrency
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA synchronous=NORMAL")
            conn.execute("PRAGMA cache_size=10000")
            yield conn
        finally:
            conn.close()
            self.active_connections -= 1
            self.connection_lock.release()
    
    def throttle_query(self):
        """Add delay between queries to prevent overwhelming database"""
        with self.lock:
            now = time.time()
            self.query_times.append(now)
            
            # If too many queries recently, add delay
            if len(self.query_times) >= 10:
                recent_queries = [t for t in self.query_times if now - t < 1.0]
                if len(recent_queries) > 5:
                    time.sleep(self.query_delay * len(recent_queries))

class ResourceManager:
    """Central resource management system"""
    
    def __init__(self):
        # Rate limiters for different operations - FULL SPEED
        self.api_limiter = RateLimiter(max_tokens=20, refill_rate=5.0)   # Much faster
        self.db_limiter = RateLimiter(max_tokens=50, refill_rate=10.0)   # Fast DB queries
        self.file_limiter = RateLimiter(max_tokens=100, refill_rate=20.0) # Fast file ops
        
        # CPU and system monitoring - MINIMAL THROTTLING
        self.cpu_throttler = CPUThrottler(cpu_threshold=90.0)  # Only throttle at 90% CPU
        self.db_throttler = DatabaseThrottler(max_connections=10)  # 10 parallel connections
        
        # Operation counters
        self.operation_counts = defaultdict(int)
        self.start_time = time.time()
        
        logger.info("Resource Manager initialized")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get resource usage statistics"""
        uptime = time.time() - self.start_time
        cpu_percent = psutil.cpu_percent()
        memory = psutil.virtual_memory()
        
        return {
            'uptime_seconds': uptime,
            'cpu_percent': cpu_percent,
            'memory_percent': memory.percent,
            'memory_available_gb': memory.available / (1024**3),
            'active_db_connections': self.db_throttler.active_connections,
            'operation_counts': dict(self.operation_counts),
            'api_tokens_available': self.api_limiter.tokens,
            'db_tokens_available': self.db_limiter.tokens
        }

# Global resource manager instance
_resource_manager = None

def get_resource_manager() -> ResourceManager:
    """Get the global resource manager instance"""
    global _resource_manager
    if _resource_manager is None:
        _resource_manager = ResourceManager()
    return _resource_manager

# Decorators for easy throttling

def throttle_api_call(func):
    """Decorator to throttle API calls"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        rm = get_resource_manager()
        rm.api_limiter.wait_for_token(timeout=30.0)
        rm.cpu_throttler.throttle_if_needed()
        rm.operation_counts['api_calls'] += 1
        
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.error(f"API call failed: {e}")
            # Add extra delay on error
            time.sleep(1.0)
            raise
    
    return wrapper

def throttle_database_operation(func):
    """Decorator to throttle database operations"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        rm = get_resource_manager()
        rm.db_limiter.wait_for_token(timeout=10.0)
        rm.db_throttler.throttle_query()
        rm.cpu_throttler.throttle_if_needed()
        rm.operation_counts['db_operations'] += 1
        
        return func(*args, **kwargs)
    
    return wrapper

def throttle_file_operation(func):
    """Decorator to throttle file operations"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        rm = get_resource_manager()
        rm.file_limiter.wait_for_token()
        rm.cpu_throttler.throttle_if_needed()
        rm.operation_counts['file_operations'] += 1
        
        return func(*args, **kwargs)
    
    return wrapper

def managed_sleep(duration: float = 0.001):
    """Smart sleep that considers system load - MINIMAL"""
    rm = get_resource_manager()
    base_sleep = duration  # No multiplication
    
    # Only slight increase if CPU is very high
    if rm.cpu_throttler.should_throttle():
        base_sleep *= 1.5  # Just 1.5x when throttling
    
    time.sleep(base_sleep)

# Context managers

@contextmanager
def managed_database_connection(db_path: str):
    """Get a managed database connection with throttling"""
    rm = get_resource_manager()
    with rm.db_throttler.get_connection(db_path) as conn:
        yield conn

def log_resource_stats():
    """Log current resource statistics"""
    rm = get_resource_manager()
    stats = rm.get_stats()
    logger.info(f"Resource Stats: CPU {stats['cpu_percent']:.1f}%, "
                f"Memory {stats['memory_percent']:.1f}%, "
                f"DB Connections {stats['active_db_connections']}, "
                f"Operations {sum(stats['operation_counts'].values())}")

if __name__ == "__main__":
    # Test the resource manager
    rm = get_resource_manager()
    
    print("Testing resource manager...")
    print(f"Initial stats: {rm.get_stats()}")
    
    # Test rate limiting
    print("\nTesting API rate limiter...")
    for i in range(3):
        if rm.api_limiter.acquire():
            print(f"API call {i+1} allowed")
        else:
            print(f"API call {i+1} rate limited")
    
    print(f"\nFinal stats: {rm.get_stats()}")