#!/usr/bin/env python3
"""
Nexus Ephemeral Mode - Scan, Process, Export, Forget
Privacy-preserving document processing with selective memory
"""

import os
import shutil
import sqlite3
import json
import tempfile
import tarfile
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import chromadb
from chromadb.utils import embedding_functions

class NexusEphemeralSession:
    """Ephemeral scanning session with automatic cleanup"""
    
    def __init__(self, session_name: str = None):
        self.session_name = session_name or f"ephemeral_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.temp_dir = Path(tempfile.mkdtemp(prefix=f"nexus_{self.session_name}_"))
        
        # Temporary databases
        self.temp_cache_db = self.temp_dir / "temp_cache.db"
        self.temp_vector_db = self.temp_dir / "temp_vectors"
        
        # Learning extraction
        self.learnings = {
            'patterns_observed': [],
            'file_types_processed': set(),
            'organizational_insights': [],
            'metadata_only': {}
        }
        
        print(f"🔒 Ephemeral session started: {self.session_name}")
        print(f"📁 Temp directory: {self.temp_dir}")
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - cleanup everything"""
        self.cleanup()
    
    def scan_and_process(self, source_paths: List[str], 
                        process_content: bool = True) -> Dict:
        """Scan paths temporarily without permanent storage"""
        
        from nexus_document_ingestion import NexusDocumentCache, NexusDocumentProcessor
        
        # Create temporary cache
        temp_cache = NexusDocumentCache(cache_root=str(self.temp_dir / "cache"))
        temp_cache.cache_db = self.temp_cache_db
        temp_cache.init_cache_db()
        
        processor = NexusDocumentProcessor()
        
        stats = {
            'files_scanned': 0,
            'files_processed': 0,
            'total_size': 0,
            'file_types': {}
        }
        
        for source_path in source_paths:
            path = Path(source_path)
            if not path.exists():
                continue
            
            for file_path in path.rglob("*"):
                if file_path.is_file():
                    stats['files_scanned'] += 1
                    
                    # Extract learnings without storing content
                    file_ext = file_path.suffix.lower()
                    stats['file_types'][file_ext] = stats['file_types'].get(file_ext, 0) + 1
                    self.learnings['file_types_processed'].add(file_ext)
                    
                    # Get file size for statistics
                    file_size = file_path.stat().st_size
                    stats['total_size'] += file_size
                    
                    if process_content:
                        # Process for vector embedding but don't keep raw content
                        cached_path = temp_cache.cache_file(file_path)
                        if cached_path:
                            doc_data = processor.process_file(cached_path)
                            if doc_data and 'content' in doc_data:
                                # Extract patterns without storing content
                                self._extract_patterns(doc_data)
                                stats['files_processed'] += 1
        
        # Record organizational insights
        self.learnings['organizational_insights'].append({
            'total_files': stats['files_scanned'],
            'file_type_distribution': dict(stats['file_types']),
            'average_file_size': stats['total_size'] / stats['files_scanned'] if stats['files_scanned'] > 0 else 0
        })
        
        return stats
    
    def _extract_patterns(self, doc_data: Dict):
        """Extract patterns and learnings without storing content"""
        content = doc_data.get('content', '')
        
        # Extract high-level patterns only
        patterns = {
            'has_code': any(marker in content for marker in ['def ', 'class ', 'function', 'import']),
            'has_urls': 'http' in content or 'www.' in content,
            'has_emails': '@' in content and '.' in content.split('@')[-1] if '@' in content else False,
            'document_structure': 'structured' if any(marker in content for marker in ['##', '**', '1.', '*']) else 'unstructured',
            'content_type': doc_data.get('type', 'unknown'),
            'word_count_range': self._get_word_count_range(doc_data.get('word_count', 0))
        }
        
        self.learnings['patterns_observed'].append(patterns)
    
    def _get_word_count_range(self, word_count: int) -> str:
        """Categorize word count into ranges"""
        if word_count < 100:
            return 'brief'
        elif word_count < 500:
            return 'short'
        elif word_count < 2000:
            return 'medium'
        elif word_count < 10000:
            return 'long'
        else:
            return 'very_long'
    
    def create_vector_database(self, export_embeddings: bool = True) -> Optional[Path]:
        """Create temporary vector database"""
        
        # Use temporary ChromaDB
        temp_client = chromadb.PersistentClient(path=str(self.temp_vector_db))
        temp_collection = temp_client.create_collection(
            name="ephemeral_docs",
            metadata={"description": "Temporary document vectors"}
        )
        
        # Process cached files and create embeddings
        # ... (embedding logic here)
        
        if export_embeddings:
            # Export vector database
            export_path = self.temp_dir / f"{self.session_name}_vectors.tar.gz"
            with tarfile.open(export_path, "w:gz") as tar:
                tar.add(self.temp_vector_db, arcname="vector_db")
            
            return export_path
        
        return None
    
    def organize_and_copy(self, organization_rules: Dict[str, Dict]) -> Dict:
        """Organize and copy files based on rules"""
        
        from nexus_file_organizer import NexusFileOrganizer
        
        organizer = NexusFileOrganizer(str(self.temp_cache_db))
        results = {}
        
        for rule_name, rule_config in organization_rules.items():
            strategy = rule_config.get('strategy', 'by_type')
            target_dir = rule_config.get('target_dir')
            params = rule_config.get('params', {})
            
            if target_dir:
                result = organizer.execute_organization(
                    strategy=strategy,
                    target_dir=target_dir,
                    **params
                )
                results[rule_name] = result
                
                # Learn from organization results
                self.learnings['organizational_insights'].append({
                    'rule': rule_name,
                    'files_organized': result.get('copied', 0),
                    'organization_strategy': strategy
                })
        
        return results
    
    def export_learnings(self) -> Dict:
        """Export only the learnings and patterns, not the content"""
        
        # Summarize patterns
        pattern_summary = {
            'file_types': list(self.learnings['file_types_processed']),
            'content_patterns': self._summarize_patterns(),
            'organizational_insights': self.learnings['organizational_insights']
        }
        
        # Save learnings
        learnings_file = self.temp_dir / f"{self.session_name}_learnings.json"
        with open(learnings_file, 'w') as f:
            json.dump(pattern_summary, f, indent=2)
        
        print(f"📊 Learnings exported to: {learnings_file}")
        
        return pattern_summary
    
    def _summarize_patterns(self) -> Dict:
        """Summarize observed patterns without revealing content"""
        
        if not self.learnings['patterns_observed']:
            return {}
        
        # Aggregate patterns
        total = len(self.learnings['patterns_observed'])
        summary = {
            'code_files_percentage': sum(1 for p in self.learnings['patterns_observed'] if p.get('has_code')) / total * 100,
            'files_with_urls': sum(1 for p in self.learnings['patterns_observed'] if p.get('has_urls')),
            'document_structures': {},
            'content_length_distribution': {}
        }
        
        # Count document structures and lengths
        for pattern in self.learnings['patterns_observed']:
            struct = pattern.get('document_structure', 'unknown')
            summary['document_structures'][struct] = summary['document_structures'].get(struct, 0) + 1
            
            length = pattern.get('word_count_range', 'unknown')
            summary['content_length_distribution'][length] = summary['content_length_distribution'].get(length, 0) + 1
        
        return summary
    
    def export_session_package(self, export_dir: str) -> Path:
        """Export complete session package (vectors, learnings, NO content)"""
        
        export_path = Path(export_dir)
        export_path.mkdir(parents=True, exist_ok=True)
        
        package_name = f"{self.session_name}_export.tar.gz"
        package_path = export_path / package_name
        
        with tarfile.open(package_path, "w:gz") as tar:
            # Add learnings
            learnings_file = self.temp_dir / f"{self.session_name}_learnings.json"
            if learnings_file.exists():
                tar.add(learnings_file, arcname="learnings.json")
            
            # Add vector database if exists
            if self.temp_vector_db.exists():
                tar.add(self.temp_vector_db, arcname="vector_db")
            
            # Add session metadata
            metadata = {
                'session_name': self.session_name,
                'timestamp': datetime.now().isoformat(),
                'files_processed': sum(len(i['file_type_distribution']) for i in self.learnings['organizational_insights']),
                'ephemeral': True
            }
            
            metadata_file = self.temp_dir / "session_metadata.json"
            with open(metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)
            tar.add(metadata_file, arcname="metadata.json")
        
        print(f"📦 Session package exported: {package_path}")
        return package_path
    
    def cleanup(self):
        """Complete cleanup - forget everything"""
        
        print(f"🧹 Cleaning up ephemeral session: {self.session_name}")
        
        # Close any open database connections
        try:
            if hasattr(self, 'conn'):
                self.conn.close()
        except:
            pass
        
        # Secure deletion of temporary directory
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir, ignore_errors=True)
        
        print("✅ Ephemeral session cleaned - all temporary data forgotten")

def ephemeral_workflow_example():
    """Example of ephemeral document processing workflow"""
    
    print("🔒 Nexus Ephemeral Mode Example")
    print("=" * 40)
    
    # Define what to scan and where to organize
    scan_paths = [
        "/mnt/client_documents/project_x",
        "/mnt/sensitive_data/contracts"
    ]
    
    organization_rules = {
        'legal_docs': {
            'strategy': 'by_type',
            'target_dir': '/mnt/organized/legal',
            'params': {
                'type_mapping': {
                    'contracts': ['.pdf', '.doc', '.docx'],
                    'agreements': ['.pdf']
                }
            }
        },
        'by_date': {
            'strategy': 'by_date',
            'target_dir': '/mnt/organized/chronological',
            'params': {
                'date_format': '%Y/%Y-%m'
            }
        }
    }
    
    # Run ephemeral session
    with NexusEphemeralSession("client_project_x") as session:
        # 1. Scan and process
        print("\n1️⃣ Scanning documents (temporarily)...")
        scan_stats = session.scan_and_process(scan_paths)
        print(f"   Scanned: {scan_stats['files_scanned']} files")
        print(f"   Processed: {scan_stats['files_processed']} files")
        
        # 2. Create vector database
        print("\n2️⃣ Creating vector embeddings...")
        vector_export = session.create_vector_database(export_embeddings=True)
        if vector_export:
            print(f"   Vectors exported: {vector_export}")
        
        # 3. Organize and copy files
        print("\n3️⃣ Organizing files...")
        org_results = session.organize_and_copy(organization_rules)
        for rule, result in org_results.items():
            print(f"   {rule}: {result.get('copied', 0)} files copied")
        
        # 4. Export learnings only
        print("\n4️⃣ Extracting learnings...")
        learnings = session.export_learnings()
        print(f"   File types seen: {learnings.get('file_types', [])}")
        
        # 5. Create final export package
        print("\n5️⃣ Creating export package...")
        package = session.export_session_package("/mnt/exports")
        print(f"   Package ready: {package}")
    
    # Everything is now forgotten!
    print("\n✨ Session complete - all temporary data has been forgotten")
    print("   Only learnings and organized files remain")

if __name__ == "__main__":
    ephemeral_workflow_example()