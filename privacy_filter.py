#!/usr/bin/env python3
"""
Privacy Filter System for SMB Nexus Ingestion
Developed by Maeve for real-time privacy protection during file ingestion
"""

import re
import sqlite3
import json
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Set
from enum import Enum
import threading

class PrivacyLevel(Enum):
    """Privacy levels for content filtering"""
    PUBLIC = 0      # No filtering
    PERSONAL = 1    # Basic PII removal
    PRIVATE = 2     # Enhanced filtering
    RESTRICTED = 3  # Heavy redaction
    BLOCKED = 4     # Complete blocking

class FileOwnership:
    """Determine file ownership from paths"""
    
    def __init__(self):
        # Common user directories patterns
        self.user_patterns = {
            'tanasi': [
                r'Tanasi/',
                r'tanasi/',
                r'/tanasi/',
                r'Tanasi\'s',
                r'tanasi\'s'
            ],
            'jonclaude': [
                r'jonclaude/',
                r'Jon Claude/',
                r'JonClaude/',
                r'/jonclaude/',
                r'Jon\'s'
            ],
            'shared': [
                r'public/',
                r'Public/',
                r'shared/',
                r'Shared/',
                r'All Work/'
            ]
        }
        
        # Compile patterns for efficiency
        self.compiled_patterns = {}
        for user, patterns in self.user_patterns.items():
            self.compiled_patterns[user] = [re.compile(pattern, re.IGNORECASE) 
                                           for pattern in patterns]
    
    def get_owner(self, file_path: str) -> str:
        """Determine file owner from path"""
        path_lower = file_path.lower()
        
        # Check each user's patterns
        for user, patterns in self.compiled_patterns.items():
            for pattern in patterns:
                if pattern.search(file_path):
                    return user
        
        # Check for browser profiles
        if 'firefox data' in path_lower or 'chrome' in path_lower:
            # Try to extract username from profile paths
            if 'tanasi' in path_lower:
                return 'tanasi'
            elif 'jonclaude' in path_lower:
                return 'jonclaude'
        
        # Default to unknown
        return 'unknown'
    
    def get_privacy_level(self, owner: str, file_type: str) -> PrivacyLevel:
        """Determine default privacy level based on owner and file type"""
        # Browser history files are always private
        if any(keyword in file_type.lower() for keyword in 
               ['history', 'cookies', 'cache', 'session', 'bookmark']):
            return PrivacyLevel.PRIVATE
        
        # Personal directories get enhanced privacy
        if owner in ['tanasi', 'unknown']:
            return PrivacyLevel.PERSONAL
        elif owner == 'jonclaude':
            return PrivacyLevel.PUBLIC
        else:
            return PrivacyLevel.PERSONAL

class PrivacyPatterns:
    """Pattern matching for sensitive content"""
    
    def __init__(self):
        # Sensitive patterns to detect
        self.patterns = {
            'ssn': re.compile(r'\b\d{3}-\d{2}-\d{4}\b'),
            'credit_card': re.compile(r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b'),
            'email': re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'),
            'phone': re.compile(r'\b(?:\+?1[-.]?)?\(?[0-9]{3}\)?[-.]?[0-9]{3}[-.]?[0-9]{4}\b'),
            'ip_address': re.compile(r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b'),
            'password': re.compile(r'(?i)(password|passwd|pwd)[\s:=]+\S+'),
            'api_key': re.compile(r'(?i)(api[_-]?key|token|secret)[\s:=]+[\w-]+'),
            'private_key': re.compile(r'-----BEGIN (RSA |EC )?PRIVATE KEY-----'),
            'url_personal': re.compile(r'https?://[^\s]+(?:facebook|twitter|instagram|linkedin)\.com/[^\s]+'),
        }
        
        # File patterns that indicate sensitive content
        self.sensitive_file_patterns = {
            'browser_history': ['history', 'places.sqlite', 'History.db'],
            'cookies': ['cookies', 'Cookies.db'],
            'passwords': ['logins.json', 'Login Data', 'passwords'],
            'bookmarks': ['bookmarks', 'Bookmarks'],
            'cache': ['cache', 'Cache'],
            'session': ['session', 'Session'],
            'config': ['.conf', '.ini', '.cfg', 'config'],
            'keys': ['.pem', '.key', '.cert', 'id_rsa'],
        }
    
    def contains_sensitive_data(self, content: str) -> Dict[str, int]:
        """Check content for sensitive patterns"""
        matches = {}
        for pattern_name, pattern in self.patterns.items():
            found = pattern.findall(content)
            if found:
                matches[pattern_name] = len(found)
        return matches
    
    def is_sensitive_file(self, file_path: str) -> Tuple[bool, str]:
        """Check if file path indicates sensitive content"""
        file_lower = file_path.lower()
        
        for category, patterns in self.sensitive_file_patterns.items():
            if any(pattern in file_lower for pattern in patterns):
                return True, category
        
        return False, ""

class ContentRedactor:
    """Redact sensitive content based on privacy level"""
    
    def __init__(self):
        self.patterns = PrivacyPatterns()
    
    def redact_content(self, content: str, privacy_level: PrivacyLevel, 
                      detected_patterns: Optional[Dict[str, int]] = None) -> str:
        """Redact content based on privacy level"""
        if privacy_level == PrivacyLevel.BLOCKED:
            return "[CONTENT BLOCKED - PRIVACY FILTER]"
        
        if privacy_level == PrivacyLevel.PUBLIC:
            return content
        
        redacted = content
        
        # Detect patterns if not provided
        if detected_patterns is None:
            detected_patterns = self.patterns.contains_sensitive_data(content)
        
        # Apply redactions based on level
        if privacy_level >= PrivacyLevel.PERSONAL:
            # Redact emails
            redacted = self.patterns.patterns['email'].sub('[EMAIL_REDACTED]', redacted)
            # Redact phone numbers
            redacted = self.patterns.patterns['phone'].sub('[PHONE_REDACTED]', redacted)
        
        if privacy_level >= PrivacyLevel.PRIVATE:
            # Redact SSNs
            redacted = self.patterns.patterns['ssn'].sub('[SSN_REDACTED]', redacted)
            # Redact credit cards
            redacted = self.patterns.patterns['credit_card'].sub('[CC_REDACTED]', redacted)
            # Redact passwords
            redacted = self.patterns.patterns['password'].sub('[PASSWORD_REDACTED]', redacted)
            # Redact API keys
            redacted = self.patterns.patterns['api_key'].sub('[API_KEY_REDACTED]', redacted)
            # Redact personal URLs
            redacted = self.patterns.patterns['url_personal'].sub('[PERSONAL_URL_REDACTED]', redacted)
        
        if privacy_level >= PrivacyLevel.RESTRICTED:
            # Heavy redaction - remove more content
            # Redact IP addresses
            redacted = self.patterns.patterns['ip_address'].sub('[IP_REDACTED]', redacted)
            # Redact private keys
            redacted = self.patterns.patterns['private_key'].sub('[PRIVATE_KEY_REDACTED]', redacted)
            
            # Truncate to summary only
            if len(redacted) > 500:
                redacted = redacted[:500] + "\n[CONTENT TRUNCATED - PRIVACY FILTER]"
        
        return redacted

class PrivacyDatabase:
    """Database for privacy settings and audit logs"""
    
    def __init__(self, db_path: str = "./privacy_filter.db"):
        self.db_path = db_path
        self.init_database()
        self._lock = threading.Lock()
    
    def init_database(self):
        """Initialize privacy database schema"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Privacy rules table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS privacy_rules (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    rule_name TEXT UNIQUE NOT NULL,
                    rule_type TEXT NOT NULL,
                    pattern TEXT,
                    action TEXT NOT NULL,
                    privacy_level INTEGER NOT NULL,
                    owner TEXT,
                    enabled BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # File privacy settings
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS file_privacy (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    file_path TEXT UNIQUE NOT NULL,
                    file_hash TEXT,
                    owner TEXT,
                    privacy_level INTEGER NOT NULL,
                    override_reason TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Privacy audit log
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS privacy_audit (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    file_path TEXT NOT NULL,
                    owner TEXT,
                    original_privacy_level INTEGER,
                    applied_privacy_level INTEGER,
                    patterns_detected TEXT,
                    action_taken TEXT,
                    redactions_made INTEGER DEFAULT 0,
                    content_hash_before TEXT,
                    content_hash_after TEXT
                )
            ''')
            
            # User privacy preferences
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_preferences (
                    username TEXT PRIMARY KEY,
                    default_privacy_level INTEGER NOT NULL,
                    auto_redact BOOLEAN DEFAULT 1,
                    notify_on_access BOOLEAN DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Insert default user preferences
            cursor.execute('''
                INSERT OR IGNORE INTO user_preferences (username, default_privacy_level)
                VALUES 
                    ('tanasi', ?),
                    ('jonclaude', ?),
                    ('unknown', ?),
                    ('shared', ?)
            ''', (PrivacyLevel.PRIVATE.value, 
                  PrivacyLevel.PUBLIC.value,
                  PrivacyLevel.PERSONAL.value,
                  PrivacyLevel.PUBLIC.value))
            
            conn.commit()
    
    def get_file_privacy_level(self, file_path: str) -> Optional[PrivacyLevel]:
        """Get privacy level for specific file"""
        with self._lock:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    'SELECT privacy_level FROM file_privacy WHERE file_path = ?',
                    (file_path,)
                )
                result = cursor.fetchone()
                if result:
                    return PrivacyLevel(result[0])
                return None
    
    def set_file_privacy_level(self, file_path: str, owner: str, 
                              privacy_level: PrivacyLevel, reason: str = None):
        """Set privacy level for specific file"""
        with self._lock:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO file_privacy 
                    (file_path, owner, privacy_level, override_reason, updated_at)
                    VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
                ''', (file_path, owner, privacy_level.value, reason))
                conn.commit()
    
    def log_privacy_action(self, file_path: str, owner: str, 
                          original_level: PrivacyLevel, applied_level: PrivacyLevel,
                          patterns_detected: Dict[str, int], action: str,
                          content_before: str = None, content_after: str = None):
        """Log privacy filtering action"""
        with self._lock:
            # Calculate content hashes
            hash_before = hashlib.sha256(content_before.encode()).hexdigest()[:16] if content_before else None
            hash_after = hashlib.sha256(content_after.encode()).hexdigest()[:16] if content_after else None
            
            # Count redactions
            redactions = 0
            if content_before and content_after:
                redactions = content_before.count('@') - content_after.count('@')  # Simple metric
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO privacy_audit 
                    (file_path, owner, original_privacy_level, applied_privacy_level,
                     patterns_detected, action_taken, redactions_made, 
                     content_hash_before, content_hash_after)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (file_path, owner, original_level.value, applied_level.value,
                      json.dumps(patterns_detected), action, redactions,
                      hash_before, hash_after))
                conn.commit()
    
    def get_audit_stats(self, hours: int = 24) -> Dict:
        """Get privacy filtering statistics"""
        with self._lock:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Total files processed
                cursor.execute('''
                    SELECT COUNT(*), SUM(redactions_made) 
                    FROM privacy_audit 
                    WHERE timestamp > datetime('now', '-{} hours')
                '''.format(hours))
                total_files, total_redactions = cursor.fetchone()
                
                # By privacy level
                cursor.execute('''
                    SELECT applied_privacy_level, COUNT(*) 
                    FROM privacy_audit 
                    WHERE timestamp > datetime('now', '-{} hours')
                    GROUP BY applied_privacy_level
                '''.format(hours))
                by_level = dict(cursor.fetchall())
                
                # By owner
                cursor.execute('''
                    SELECT owner, COUNT(*) 
                    FROM privacy_audit 
                    WHERE timestamp > datetime('now', '-{} hours')
                    GROUP BY owner
                '''.format(hours))
                by_owner = dict(cursor.fetchall())
                
                # Patterns detected
                cursor.execute('''
                    SELECT patterns_detected 
                    FROM privacy_audit 
                    WHERE timestamp > datetime('now', '-{} hours')
                    AND patterns_detected != '{}'
                '''.format(hours))
                
                pattern_counts = {}
                for row in cursor.fetchall():
                    patterns = json.loads(row[0])
                    for pattern, count in patterns.items():
                        pattern_counts[pattern] = pattern_counts.get(pattern, 0) + count
                
                return {
                    'total_files': total_files or 0,
                    'total_redactions': total_redactions or 0,
                    'by_privacy_level': by_level,
                    'by_owner': by_owner,
                    'patterns_detected': pattern_counts
                }

class PrivacyFilter:
    """Main privacy filter system"""
    
    def __init__(self, db_path: str = "./privacy_filter.db"):
        self.ownership = FileOwnership()
        self.patterns = PrivacyPatterns()
        self.redactor = ContentRedactor()
        self.database = PrivacyDatabase(db_path)
        
        # Cache for performance
        self._cache = {}
        self._cache_lock = threading.Lock()
        
        # Statistics
        self.stats = {
            'files_processed': 0,
            'files_blocked': 0,
            'files_redacted': 0,
            'patterns_found': 0
        }
    
    def should_process_file(self, file_path: str) -> Tuple[bool, PrivacyLevel, str]:
        """Determine if file should be processed and at what privacy level"""
        # Check if it's a sensitive file type
        is_sensitive, category = self.patterns.is_sensitive_file(file_path)
        
        # Get file owner
        owner = self.ownership.get_owner(file_path)
        
        # Check for specific file privacy setting
        specific_level = self.database.get_file_privacy_level(file_path)
        if specific_level:
            if specific_level == PrivacyLevel.BLOCKED:
                return False, specific_level, owner
            return True, specific_level, owner
        
        # Determine privacy level
        if is_sensitive:
            # Sensitive files get higher privacy
            if category in ['browser_history', 'passwords', 'cookies']:
                privacy_level = PrivacyLevel.PRIVATE
            elif category in ['keys', 'config']:
                privacy_level = PrivacyLevel.RESTRICTED
            else:
                privacy_level = PrivacyLevel.PERSONAL
        else:
            # Use default based on owner
            privacy_level = self.ownership.get_privacy_level(owner, file_path)
        
        return True, privacy_level, owner
    
    def filter_content(self, file_path: str, content: str, 
                      metadata: Optional[Dict] = None) -> Tuple[str, Dict]:
        """Filter content based on privacy rules"""
        # Check cache
        cache_key = hashlib.md5(f"{file_path}{content[:100]}".encode()).hexdigest()
        with self._cache_lock:
            if cache_key in self._cache:
                self.stats['files_processed'] += 1
                return self._cache[cache_key]
        
        # Determine if we should process
        should_process, privacy_level, owner = self.should_process_file(file_path)
        
        if not should_process:
            self.stats['files_blocked'] += 1
            self.database.log_privacy_action(
                file_path, owner, privacy_level, privacy_level,
                {}, 'blocked', content, None
            )
            return None, {'blocked': True, 'reason': 'privacy_filter'}
        
        # Detect sensitive patterns
        patterns_detected = self.patterns.contains_sensitive_data(content)
        if patterns_detected:
            self.stats['patterns_found'] += len(patterns_detected)
        
        # Apply redaction
        original_level = privacy_level
        if patterns_detected and privacy_level < PrivacyLevel.PRIVATE:
            # Upgrade privacy level if sensitive data detected
            privacy_level = PrivacyLevel.PRIVATE
        
        filtered_content = self.redactor.redact_content(content, privacy_level, patterns_detected)
        
        # Create metadata
        filter_metadata = {
            'filtered': filtered_content != content,
            'owner': owner,
            'privacy_level': privacy_level.name,
            'original_privacy_level': original_level.name,
            'patterns_detected': list(patterns_detected.keys()) if patterns_detected else [],
            'redactions_made': content.count('@') - filtered_content.count('@') if '@' in content else 0
        }
        
        if metadata:
            filter_metadata.update(metadata)
        
        # Log action
        if filtered_content != content:
            self.stats['files_redacted'] += 1
            action = 'redacted'
        else:
            action = 'passed'
        
        self.database.log_privacy_action(
            file_path, owner, original_level, privacy_level,
            patterns_detected, action, content, filtered_content
        )
        
        # Cache result
        with self._cache_lock:
            self._cache[cache_key] = (filtered_content, filter_metadata)
            # Limit cache size
            if len(self._cache) > 1000:
                self._cache.clear()
        
        self.stats['files_processed'] += 1
        return filtered_content, filter_metadata
    
    def get_stats(self) -> Dict:
        """Get current filter statistics"""
        db_stats = self.database.get_audit_stats(1)  # Last hour
        return {
            **self.stats,
            **db_stats
        }
    
    def update_privacy_rule(self, file_pattern: str, privacy_level: PrivacyLevel, 
                           owner: Optional[str] = None):
        """Update privacy rule for file pattern"""
        # This would update the database rules
        # Implementation depends on specific requirements
        pass

# Integration helper for SMB ingestion
class SMBPrivacyIntegration:
    """Helper class to integrate privacy filtering with SMB ingestion"""
    
    def __init__(self, privacy_filter: PrivacyFilter):
        self.filter = privacy_filter
    
    def process_document(self, doc_data: Dict, smb_path: str) -> Optional[Dict]:
        """Process document through privacy filter"""
        if 'content' not in doc_data:
            return doc_data
        
        # Filter content
        filtered_content, metadata = self.filter.filter_content(
            smb_path, 
            doc_data['content'],
            {'file_type': doc_data.get('file_type', ''),
             'file_size': doc_data.get('file_size', 0)}
        )
        
        if filtered_content is None:
            # File was blocked
            return None
        
        # Update document data
        doc_data['content'] = filtered_content
        doc_data['privacy_metadata'] = metadata
        
        # Filter chunks if present
        if 'chunks' in doc_data and doc_data['chunks']:
            filtered_chunks = []
            for chunk in doc_data['chunks']:
                filtered_chunk, _ = self.filter.filter_content(
                    smb_path + f"_chunk_{len(filtered_chunks)}", 
                    chunk
                )
                if filtered_chunk:
                    filtered_chunks.append(filtered_chunk)
            doc_data['chunks'] = filtered_chunks
        
        return doc_data

def main():
    """Test privacy filter system"""
    print("🔐 Privacy Filter System Test")
    print("=" * 50)
    
    # Initialize filter
    filter_system = PrivacyFilter()
    
    # Test file paths
    test_files = [
        ("SYNSRT/Tanasi/Desktop/passwords.txt", "My password is secret123!"),
        ("SYNSRT/JonClaude/Documents/project.txt", "Contact john@example.com at 555-1234"),
        ("SYNSRT/Tanasi/Firefox Data/history.db", "Visited https://facebook.com/profile123"),
        ("SYNSRT/shared/public/readme.txt", "This is public information"),
    ]
    
    for file_path, content in test_files:
        print(f"\n📄 Testing: {file_path}")
        filtered, metadata = filter_system.filter_content(file_path, content)
        
        print(f"   Owner: {metadata['owner']}")
        print(f"   Privacy Level: {metadata['privacy_level']}")
        print(f"   Filtered: {metadata['filtered']}")
        if metadata['patterns_detected']:
            print(f"   Patterns: {', '.join(metadata['patterns_detected'])}")
        
        if filtered != content:
            print(f"   Original: {content[:50]}...")
            print(f"   Filtered: {filtered[:50]}...")
    
    # Show statistics
    print("\n📊 Filter Statistics:")
    stats = filter_system.get_stats()
    for key, value in stats.items():
        print(f"   {key}: {value}")

if __name__ == "__main__":
    main()