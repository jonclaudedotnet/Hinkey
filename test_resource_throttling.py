#!/usr/bin/env python3
"""
Load Testing Script for Dolores Resource Throttling System
Tests CPU throttling, rate limiting, and database connection management
"""

import time
import threading
import random
from concurrent.futures import ThreadPoolExecutor, as_completed
from dolores_core import DoloresMemory, DoloresHost
from resource_manager import get_resource_manager, log_resource_stats

class LoadTester:
    """Load testing for resource management"""
    
    def __init__(self):
        self.dolores_memory = DoloresMemory()
        self.rm = get_resource_manager()
        self.results = []
        
    def memory_stress_test(self, thread_id: int, operations: int = 10):
        """Stress test memory operations"""
        results = []
        for i in range(operations):
            start_time = time.time()
            
            # Random memory operations
            operation_type = random.choice(['remember', 'recall', 'stats'])
            
            try:
                if operation_type == 'remember':
                    content = f"Test content from thread {thread_id}, operation {i}"
                    category = random.choice(['test', 'load', 'stress'])
                    success = self.dolores_memory.remember(content, category)
                    operation = f"remember: {success}"
                    
                elif operation_type == 'recall':
                    query = random.choice(['test', 'thread', 'content', 'operation'])
                    memories = self.dolores_memory.recall(query, limit=5)
                    operation = f"recall: {len(memories)} results"
                    
                elif operation_type == 'stats':
                    stats = self.dolores_memory.get_memory_stats()
                    operation = f"stats: {stats['total_memories']} memories"
                
                duration = time.time() - start_time
                results.append({
                    'thread_id': thread_id,
                    'operation': operation,
                    'duration': duration,
                    'success': True
                })
                
            except Exception as e:
                duration = time.time() - start_time
                results.append({
                    'thread_id': thread_id,
                    'operation': f"ERROR: {str(e)}",
                    'duration': duration,
                    'success': False
                })
            
            # Small delay between operations
            time.sleep(0.1)
        
        return results
    
    def api_simulation_test(self, thread_id: int, calls: int = 5):
        """Simulate API calls to test rate limiting"""
        results = []
        
        for i in range(calls):
            start_time = time.time()
            
            try:
                # Test if we can acquire API token
                if self.rm.api_limiter.acquire():
                    # Simulate API processing time
                    time.sleep(random.uniform(0.5, 2.0))
                    operation = "API call successful"
                    success = True
                else:
                    operation = "API call rate limited"
                    success = False
                
                duration = time.time() - start_time
                results.append({
                    'thread_id': thread_id,
                    'operation': operation,
                    'duration': duration,
                    'success': success
                })
                
            except Exception as e:
                duration = time.time() - start_time
                results.append({
                    'thread_id': thread_id,
                    'operation': f"API ERROR: {str(e)}",
                    'duration': duration,
                    'success': False
                })
        
        return results
    
    def run_load_test(self, threads: int = 5, operations_per_thread: int = 10):
        """Run comprehensive load test"""
        print(f"🧪 Starting load test with {threads} threads, {operations_per_thread} operations each")
        print("=" * 60)
        
        # Initial stats
        initial_stats = self.rm.get_stats()
        print(f"Initial stats: {sum(initial_stats['operation_counts'].values())} operations")
        
        start_time = time.time()
        all_results = []
        
        # Run memory stress test
        print("\n📊 Running memory stress test...")
        with ThreadPoolExecutor(max_workers=threads) as executor:
            memory_futures = [
                executor.submit(self.memory_stress_test, i, operations_per_thread)
                for i in range(threads)
            ]
            
            for future in as_completed(memory_futures):
                try:
                    results = future.result()
                    all_results.extend(results)
                except Exception as e:
                    print(f"Thread failed: {e}")
        
        # Run API simulation test
        print("\n🌐 Running API rate limiting test...")
        with ThreadPoolExecutor(max_workers=threads) as executor:
            api_futures = [
                executor.submit(self.api_simulation_test, i, 3)
                for i in range(threads)
            ]
            
            for future in as_completed(api_futures):
                try:
                    results = future.result()
                    all_results.extend(results)
                except Exception as e:
                    print(f"API thread failed: {e}")
        
        total_duration = time.time() - start_time
        
        # Analyze results
        self.analyze_results(all_results, total_duration)
    
    def analyze_results(self, results, total_duration):
        """Analyze load test results"""
        print("\n📈 LOAD TEST RESULTS")
        print("=" * 60)
        
        successful_ops = [r for r in results if r['success']]
        failed_ops = [r for r in results if not r['success']]
        
        print(f"Total operations:    {len(results)}")
        print(f"Successful:          {len(successful_ops)} ({len(successful_ops)/len(results)*100:.1f}%)")
        print(f"Failed/Throttled:    {len(failed_ops)} ({len(failed_ops)/len(results)*100:.1f}%)")
        print(f"Total duration:      {total_duration:.2f} seconds")
        print(f"Operations/second:   {len(results)/total_duration:.1f}")
        
        if successful_ops:
            avg_duration = sum(r['duration'] for r in successful_ops) / len(successful_ops)
            max_duration = max(r['duration'] for r in successful_ops)
            min_duration = min(r['duration'] for r in successful_ops)
            
            print(f"\nOperation timings:")
            print(f"  Average:  {avg_duration:.3f} seconds")
            print(f"  Maximum:  {max_duration:.3f} seconds")
            print(f"  Minimum:  {min_duration:.3f} seconds")
        
        # Operation breakdown
        operation_types = {}
        for result in results:
            op_type = result['operation'].split(':')[0]
            if op_type not in operation_types:
                operation_types[op_type] = {'count': 0, 'success': 0}
            operation_types[op_type]['count'] += 1
            if result['success']:
                operation_types[op_type]['success'] += 1
        
        print(f"\nOperation breakdown:")
        for op_type, stats in operation_types.items():
            success_rate = (stats['success'] / stats['count']) * 100
            print(f"  {op_type:15}: {stats['count']:3d} ops, {success_rate:5.1f}% success")
        
        # Final system stats
        final_stats = self.rm.get_stats()
        print(f"\nSystem state after test:")
        log_resource_stats()
        print(f"Total operations recorded: {sum(final_stats['operation_counts'].values())}")
        
        # Performance assessment
        print(f"\n🎯 PERFORMANCE ASSESSMENT")
        if len(failed_ops) / len(results) < 0.1:
            print("   ✅ Excellent: Less than 10% operations throttled")
        elif len(failed_ops) / len(results) < 0.3:
            print("   ⚠️  Good: Moderate throttling observed")
        else:
            print("   🔴 Heavy throttling - consider adjusting limits")
        
        if avg_duration < 0.1:
            print("   ✅ Fast response times")
        elif avg_duration < 0.5:
            print("   ⚠️  Moderate response times")
        else:
            print("   🔴 Slow response times - check system load")

def quick_throttle_test():
    """Quick test of throttling mechanisms"""
    print("🏃 Quick throttle test...")
    
    rm = get_resource_manager()
    
    # Test API rate limiter
    print("\nTesting API rate limiter (5 rapid calls):")
    api_successes = 0
    for i in range(5):
        if rm.api_limiter.acquire():
            print(f"  Call {i+1}: ✅ Allowed")
            api_successes += 1
        else:
            print(f"  Call {i+1}: 🔴 Rate limited")
    
    print(f"API calls allowed: {api_successes}/5")
    
    # Test database rate limiter
    print("\nTesting DB rate limiter (10 rapid queries):")
    db_successes = 0
    for i in range(10):
        if rm.db_limiter.acquire():
            db_successes += 1
        time.sleep(0.05)
    
    print(f"DB queries allowed: {db_successes}/10")
    
    # Show current stats
    print("\nCurrent resource stats:")
    log_resource_stats()

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "quick":
        quick_throttle_test()
    else:
        print("Dolores Resource Throttling Load Test")
        print("This will stress test the resource management system.")
        print("Monitor with: python3 resource_monitor.py")
        print()
        
        response = input("Run full load test? (y/n): ")
        if response.lower() == 'y':
            tester = LoadTester()
            tester.run_load_test(threads=3, operations_per_thread=5)
        else:
            quick_throttle_test()