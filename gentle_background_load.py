#!/usr/bin/env python3
"""
Gentle Background Load Generator for Dolores System
Maintains a light, video-friendly CPU load around 20-30%
"""

import time
import threading
import math
import random
import psutil
from resource_manager import get_resource_manager, managed_sleep

class GentleLoadGenerator:
    """Generate a controlled, gentle CPU load"""
    
    def __init__(self, target_cpu: float = 25.0):
        self.target_cpu = target_cpu
        self.running = False
        self.threads = []
        self.load_adjustment = 1.0
        self.rm = get_resource_manager()
        
    def calculate_pi_digits(self, iterations: int):
        """Light mathematical computation"""
        # Machin's formula for pi - gentle on CPU
        result = 0
        for k in range(iterations):
            result += ((-1)**k) / (2*k + 1)
            # Frequent yields to avoid blocking
            if k % 100 == 0:
                time.sleep(0.001)
        return result * 4
    
    def memory_shuffle(self, size: int = 1000):
        """Light memory operations"""
        data = list(range(size))
        for _ in range(10):
            random.shuffle(data)
            time.sleep(0.01)
        return sum(data)
    
    def worker_thread(self, thread_id: int):
        """Worker thread that generates controlled load"""
        print(f"Worker {thread_id} started")
        
        while self.running:
            try:
                # Check current CPU usage
                cpu_percent = psutil.cpu_percent(interval=0.1)
                
                # Adjust load based on current CPU
                if cpu_percent > self.target_cpu + 5:
                    # Too high - back off significantly
                    self.load_adjustment *= 0.7
                    time.sleep(2.0)  # Long pause
                elif cpu_percent < self.target_cpu - 5:
                    # Too low - increase slightly
                    self.load_adjustment *= 1.1
                    self.load_adjustment = min(self.load_adjustment, 2.0)
                
                # Perform light work based on adjustment
                work_iterations = int(100 * self.load_adjustment)
                
                # Mix of different operations
                operation = random.choice(['pi', 'memory', 'sleep'])
                
                if operation == 'pi':
                    self.calculate_pi_digits(work_iterations)
                elif operation == 'memory':
                    self.memory_shuffle(work_iterations)
                else:
                    # Just sleep - very gentle
                    time.sleep(0.5)
                
                # Always pause between operations
                managed_sleep(0.2)
                
            except Exception as e:
                print(f"Worker {thread_id} error: {e}")
                time.sleep(1.0)
    
    def start(self, num_threads: int = 2):
        """Start the gentle load generator"""
        self.running = True
        
        print(f"Starting gentle load generator with {num_threads} threads")
        print(f"Target CPU: {self.target_cpu}%")
        print("This is designed to be video-friendly!")
        print("Press Ctrl+C to stop\n")
        
        for i in range(num_threads):
            thread = threading.Thread(target=self.worker_thread, args=(i,))
            thread.daemon = True
            thread.start()
            self.threads.append(thread)
            time.sleep(0.5)  # Stagger thread starts
    
    def stop(self):
        """Stop all worker threads"""
        print("\nStopping gentle load generator...")
        self.running = False
        for thread in self.threads:
            thread.join(timeout=2.0)
        print("All workers stopped")
    
    def monitor_loop(self):
        """Monitor and display stats"""
        try:
            while self.running:
                cpu_percent = psutil.cpu_percent(interval=1)
                memory = psutil.virtual_memory()
                
                # Clear line and print stats
                print(f"\rCPU: {cpu_percent:5.1f}% (target: {self.target_cpu}%) | "
                      f"Memory: {memory.percent:5.1f}% | "
                      f"Load adjustment: {self.load_adjustment:.2f} | "
                      f"Video-friendly mode ✓", end='', flush=True)
                
                time.sleep(2.0)
                
        except KeyboardInterrupt:
            pass

def main():
    """Run the gentle background load generator"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Gentle background load for video playback')
    parser.add_argument('--target-cpu', type=float, default=25.0,
                       help='Target CPU percentage (default: 25%)')
    parser.add_argument('--threads', type=int, default=2,
                       help='Number of worker threads (default: 2)')
    
    args = parser.parse_args()
    
    # Ensure target is reasonable for video playback
    if args.target_cpu > 40:
        print("Warning: Target CPU > 40% may interfere with video playback")
        response = input("Continue anyway? (y/n): ")
        if response.lower() != 'y':
            return
    
    generator = GentleLoadGenerator(target_cpu=args.target_cpu)
    
    try:
        generator.start(num_threads=args.threads)
        generator.monitor_loop()
    except KeyboardInterrupt:
        pass
    finally:
        generator.stop()
        
        # Final stats
        print(f"\n\nFinal statistics:")
        stats = generator.rm.get_stats()
        print(f"Total operations: {sum(stats['operation_counts'].values())}")
        print(f"Uptime: {stats['uptime_seconds']:.0f} seconds")
        print("\nVideo playback should now be smooth!")

if __name__ == "__main__":
    main()