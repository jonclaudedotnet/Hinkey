#!/usr/bin/env python3
"""
Privacy Filter API - RESTful endpoints for privacy control panel
Developed by Maeve for real-time privacy management
"""

from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
import sqlite3
import json
from datetime import datetime, timedelta
from privacy_filter import PrivacyFilter, PrivacyLevel, PrivacyDatabase
import threading
import os

app = Flask(__name__)
CORS(app)  # Enable CORS for control panel

# Global privacy filter instance
privacy_filter = PrivacyFilter()
privacy_db = PrivacyDatabase()

# Lock for thread safety
api_lock = threading.Lock()

# HTML template for web interface
CONTROL_PANEL_HTML = '''
<!DOCTYPE html>
<html>
<head>
    <title>Privacy Filter Control Panel</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        h1 { color: #333; border-bottom: 2px solid #4CAF50; padding-bottom: 10px; }
        .stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin: 20px 0; }
        .stat-card { background: #f9f9f9; padding: 15px; border-radius: 5px; border-left: 4px solid #4CAF50; }
        .stat-value { font-size: 24px; font-weight: bold; color: #333; }
        .stat-label { color: #666; font-size: 14px; }
        table { width: 100%; border-collapse: collapse; margin: 20px 0; }
        th, td { padding: 10px; text-align: left; border-bottom: 1px solid #ddd; }
        th { background: #4CAF50; color: white; }
        tr:hover { background: #f5f5f5; }
        .privacy-level { padding: 3px 8px; border-radius: 3px; font-size: 12px; }
        .level-PUBLIC { background: #4CAF50; color: white; }
        .level-PERSONAL { background: #FF9800; color: white; }
        .level-PRIVATE { background: #F44336; color: white; }
        .level-RESTRICTED { background: #9C27B0; color: white; }
        .level-BLOCKED { background: #000; color: white; }
        .controls { margin: 20px 0; }
        button { background: #4CAF50; color: white; border: none; padding: 10px 20px; border-radius: 4px; cursor: pointer; margin-right: 10px; }
        button:hover { background: #45a049; }
        .refresh-btn { background: #2196F3; }
        .clear-btn { background: #F44336; }
        input[type="text"] { padding: 8px; margin: 5px; border: 1px solid #ddd; border-radius: 4px; }
        select { padding: 8px; margin: 5px; border: 1px solid #ddd; border-radius: 4px; }
        .pattern-tag { background: #e0e0e0; padding: 2px 6px; border-radius: 3px; margin: 2px; display: inline-block; font-size: 12px; }
    </style>
    <script>
        function refreshData() {
            fetch('/api/stats')
                .then(response => response.json())
                .then(data => {
                    document.getElementById('total-files').textContent = data.total_files || 0;
                    document.getElementById('files-blocked').textContent = data.files_blocked || 0;
                    document.getElementById('files-redacted').textContent = data.files_redacted || 0;
                    document.getElementById('patterns-found').textContent = data.patterns_found || 0;
                });
            
            fetch('/api/audit/recent')
                .then(response => response.json())
                .then(data => {
                    updateAuditTable(data.audits);
                });
        }
        
        function updateAuditTable(audits) {
            const tbody = document.getElementById('audit-tbody');
            tbody.innerHTML = '';
            
            audits.forEach(audit => {
                const row = tbody.insertRow();
                row.innerHTML = `
                    <td>${new Date(audit.timestamp).toLocaleString()}</td>
                    <td title="${audit.file_path}">${audit.file_path.split('/').pop()}</td>
                    <td>${audit.owner}</td>
                    <td><span class="privacy-level level-${audit.privacy_level}">${audit.privacy_level}</span></td>
                    <td>${audit.action}</td>
                    <td>${audit.patterns ? audit.patterns.map(p => `<span class="pattern-tag">${p}</span>`).join('') : '-'}</td>
                `;
            });
        }
        
        function updateRule() {
            const pattern = document.getElementById('rule-pattern').value;
            const level = document.getElementById('rule-level').value;
            
            if (!pattern) {
                alert('Please enter a file pattern');
                return;
            }
            
            fetch('/api/rules', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    pattern: pattern,
                    privacy_level: level
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    alert('Rule updated successfully');
                    document.getElementById('rule-pattern').value = '';
                }
            });
        }
        
        function clearCache() {
            if (confirm('Clear privacy filter cache?')) {
                fetch('/api/cache/clear', {method: 'POST'})
                    .then(() => {
                        alert('Cache cleared');
                        refreshData();
                    });
            }
        }
        
        // Auto-refresh every 5 seconds
        setInterval(refreshData, 5000);
        
        // Initial load
        window.onload = refreshData;
    </script>
</head>
<body>
    <div class="container">
        <h1>🔐 Privacy Filter Control Panel</h1>
        
        <div class="controls">
            <button class="refresh-btn" onclick="refreshData()">🔄 Refresh</button>
            <button class="clear-btn" onclick="clearCache()">🗑️ Clear Cache</button>
        </div>
        
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-value" id="total-files">0</div>
                <div class="stat-label">Files Processed</div>
            </div>
            <div class="stat-card">
                <div class="stat-value" id="files-blocked">0</div>
                <div class="stat-label">Files Blocked</div>
            </div>
            <div class="stat-card">
                <div class="stat-value" id="files-redacted">0</div>
                <div class="stat-label">Files Redacted</div>
            </div>
            <div class="stat-card">
                <div class="stat-value" id="patterns-found">0</div>
                <div class="stat-label">Patterns Detected</div>
            </div>
        </div>
        
        <h2>Add Privacy Rule</h2>
        <div>
            <input type="text" id="rule-pattern" placeholder="File pattern (e.g., */passwords/*)" style="width: 300px;">
            <select id="rule-level">
                <option value="PUBLIC">Public</option>
                <option value="PERSONAL">Personal</option>
                <option value="PRIVATE" selected>Private</option>
                <option value="RESTRICTED">Restricted</option>
                <option value="BLOCKED">Blocked</option>
            </select>
            <button onclick="updateRule()">Add Rule</button>
        </div>
        
        <h2>Recent Privacy Actions</h2>
        <table>
            <thead>
                <tr>
                    <th>Timestamp</th>
                    <th>File</th>
                    <th>Owner</th>
                    <th>Privacy Level</th>
                    <th>Action</th>
                    <th>Patterns Detected</th>
                </tr>
            </thead>
            <tbody id="audit-tbody">
                <!-- Populated by JavaScript -->
            </tbody>
        </table>
    </div>
</body>
</html>
'''

@app.route('/')
def index():
    """Serve the control panel web interface"""
    return render_template_string(CONTROL_PANEL_HTML)

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Get current privacy filter statistics"""
    with api_lock:
        stats = privacy_filter.get_stats()
        return jsonify(stats)

@app.route('/api/audit/recent', methods=['GET'])
def get_recent_audits():
    """Get recent privacy audit entries"""
    limit = request.args.get('limit', 50, type=int)
    
    with api_lock:
        conn = sqlite3.connect(privacy_db.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT timestamp, file_path, owner, applied_privacy_level, 
                   action_taken, patterns_detected, redactions_made
            FROM privacy_audit
            ORDER BY timestamp DESC
            LIMIT ?
        ''', (limit,))
        
        audits = []
        for row in cursor.fetchall():
            privacy_level_name = PrivacyLevel(row[3]).name
            patterns = json.loads(row[5]) if row[5] else {}
            
            audits.append({
                'timestamp': row[0],
                'file_path': row[1],
                'owner': row[2],
                'privacy_level': privacy_level_name,
                'action': row[4],
                'patterns': list(patterns.keys()) if patterns else [],
                'redactions': row[6]
            })
        
        conn.close()
        
    return jsonify({'audits': audits})

@app.route('/api/rules', methods=['GET', 'POST'])
def manage_rules():
    """Get or create privacy rules"""
    if request.method == 'GET':
        with api_lock:
            conn = sqlite3.connect(privacy_db.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT rule_name, rule_type, pattern, action, privacy_level, owner, enabled
                FROM privacy_rules
                WHERE enabled = 1
                ORDER BY created_at DESC
            ''')
            
            rules = []
            for row in cursor.fetchall():
                rules.append({
                    'name': row[0],
                    'type': row[1],
                    'pattern': row[2],
                    'action': row[3],
                    'privacy_level': PrivacyLevel(row[4]).name,
                    'owner': row[5],
                    'enabled': row[6]
                })
            
            conn.close()
            
        return jsonify({'rules': rules})
    
    else:  # POST
        data = request.json
        pattern = data.get('pattern')
        privacy_level = data.get('privacy_level', 'PRIVATE')
        
        if not pattern:
            return jsonify({'status': 'error', 'message': 'Pattern required'}), 400
        
        try:
            level = PrivacyLevel[privacy_level]
        except KeyError:
            return jsonify({'status': 'error', 'message': 'Invalid privacy level'}), 400
        
        with api_lock:
            conn = sqlite3.connect(privacy_db.db_path)
            cursor = conn.cursor()
            
            rule_name = f"rule_{pattern.replace('/', '_').replace('*', 'star')}"
            
            cursor.execute('''
                INSERT OR REPLACE INTO privacy_rules 
                (rule_name, rule_type, pattern, action, privacy_level, updated_at)
                VALUES (?, 'path_pattern', ?, 'apply_level', ?, CURRENT_TIMESTAMP)
            ''', (rule_name, pattern, level.value))
            
            conn.commit()
            conn.close()
            
            # Update filter (in production, this would reload rules)
            privacy_filter.update_privacy_rule(pattern, level)
        
        return jsonify({'status': 'success', 'rule': rule_name})

@app.route('/api/files/<path:file_path>/privacy', methods=['GET', 'PUT'])
def file_privacy(file_path):
    """Get or update privacy settings for specific file"""
    if request.method == 'GET':
        with api_lock:
            level = privacy_db.get_file_privacy_level(file_path)
            
        if level:
            return jsonify({
                'file_path': file_path,
                'privacy_level': level.name
            })
        else:
            return jsonify({
                'file_path': file_path,
                'privacy_level': 'DEFAULT'
            })
    
    else:  # PUT
        data = request.json
        privacy_level = data.get('privacy_level')
        reason = data.get('reason', '')
        
        try:
            level = PrivacyLevel[privacy_level]
        except KeyError:
            return jsonify({'status': 'error', 'message': 'Invalid privacy level'}), 400
        
        # Determine owner
        owner = privacy_filter.ownership.get_owner(file_path)
        
        with api_lock:
            privacy_db.set_file_privacy_level(file_path, owner, level, reason)
        
        return jsonify({
            'status': 'success',
            'file_path': file_path,
            'privacy_level': level.name
        })

@app.route('/api/users/<username>/preferences', methods=['GET', 'PUT'])
def user_preferences(username):
    """Get or update user privacy preferences"""
    if request.method == 'GET':
        with api_lock:
            conn = sqlite3.connect(privacy_db.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT default_privacy_level, auto_redact, notify_on_access
                FROM user_preferences
                WHERE username = ?
            ''', (username,))
            
            result = cursor.fetchone()
            conn.close()
            
        if result:
            return jsonify({
                'username': username,
                'default_privacy_level': PrivacyLevel(result[0]).name,
                'auto_redact': bool(result[1]),
                'notify_on_access': bool(result[2])
            })
        else:
            return jsonify({'status': 'error', 'message': 'User not found'}), 404
    
    else:  # PUT
        data = request.json
        
        updates = []
        params = []
        
        if 'default_privacy_level' in data:
            try:
                level = PrivacyLevel[data['default_privacy_level']]
                updates.append('default_privacy_level = ?')
                params.append(level.value)
            except KeyError:
                return jsonify({'status': 'error', 'message': 'Invalid privacy level'}), 400
        
        if 'auto_redact' in data:
            updates.append('auto_redact = ?')
            params.append(int(data['auto_redact']))
        
        if 'notify_on_access' in data:
            updates.append('notify_on_access = ?')
            params.append(int(data['notify_on_access']))
        
        if not updates:
            return jsonify({'status': 'error', 'message': 'No updates provided'}), 400
        
        updates.append('updated_at = CURRENT_TIMESTAMP')
        params.append(username)
        
        with api_lock:
            conn = sqlite3.connect(privacy_db.db_path)
            cursor = conn.cursor()
            
            query = f"UPDATE user_preferences SET {', '.join(updates)} WHERE username = ?"
            cursor.execute(query, params)
            
            conn.commit()
            conn.close()
        
        return jsonify({'status': 'success', 'username': username})

@app.route('/api/cache/clear', methods=['POST'])
def clear_cache():
    """Clear the privacy filter cache"""
    with api_lock:
        with privacy_filter._cache_lock:
            privacy_filter._cache.clear()
        
    return jsonify({'status': 'success', 'message': 'Cache cleared'})

@app.route('/api/test', methods=['POST'])
def test_filter():
    """Test privacy filter on sample content"""
    data = request.json
    file_path = data.get('file_path', 'test/sample.txt')
    content = data.get('content', '')
    
    if not content:
        return jsonify({'status': 'error', 'message': 'Content required'}), 400
    
    with api_lock:
        filtered_content, metadata = privacy_filter.filter_content(file_path, content)
    
    return jsonify({
        'original_content': content,
        'filtered_content': filtered_content,
        'metadata': metadata
    })

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'privacy_filter_api',
        'timestamp': datetime.now().isoformat()
    })

def run_api(host='0.0.0.0', port=5001, debug=False):
    """Run the privacy filter API server"""
    print(f"🔐 Privacy Filter API starting on http://{host}:{port}")
    print(f"📊 Control Panel: http://{host}:{port}/")
    app.run(host=host, port=port, debug=debug)

if __name__ == '__main__':
    run_api(debug=True)