#!/usr/bin/env python3
"""
Simple teaching interface for Dolores
"""

from dolores_core import initialize_dolores, teach_dolores
from resource_manager import get_resource_manager, log_resource_stats

def main():
    print("Initializing Dolores...")
    dolores = initialize_dolores()
    
    print("\nDolores is ready to learn!")
    print("Type 'quit' to exit, 'stats' for memory stats, 'resources' for system stats")
    print("-" * 50)
    
    teaching_count = 0
    while True:
        user_input = input("\nTeach Dolores: ")
        
        if user_input.lower() == 'quit':
            break
        elif user_input.lower() == 'stats':
            stats = dolores.memory.get_memory_stats()
            print(f"\nDolores's Memory Stats:")
            print(f"Total memories: {stats['total_memories']}")
            print(f"Categories: {stats['categories']}")
            print(f"Family connections: {stats['total_relationships']}")
            print(f"Storage used: {stats['storage_used_mb']:.2f} MB")
        elif user_input.lower() == 'resources':
            log_resource_stats()
            rm = get_resource_manager()
            resource_stats = rm.get_stats()
            print(f"\nResource Usage:")
            print(f"Operations: {sum(resource_stats['operation_counts'].values())}")
            print(f"Available tokens - API: {resource_stats['api_tokens_available']:.1f}, DB: {resource_stats['db_tokens_available']:.1f}")
        else:
            teach_dolores(dolores, user_input)
            teaching_count += 1
            
            # Log resources every 5 teachings
            if teaching_count % 5 == 0:
                log_resource_stats()

if __name__ == "__main__":
    main()