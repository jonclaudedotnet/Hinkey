#!/bin/bash
# Setup automated Synology backups for Dolores

echo "🔧 Setting up Dolores Synology backup automation"
echo "=============================================="

# Create backup script
cat > dolores_daily_backup.sh << 'EOF'
#!/bin/bash
# Daily backup of Dolores's knowledge to Synology

cd /home/jonclaude/agents/Hinkey

# Log file
LOG_FILE="./backup_logs/dolores_backup_$(date +%Y%m%d).log"
mkdir -p backup_logs

echo "Starting Dolores backup at $(date)" >> $LOG_FILE

# Run backup
python3 synology_backup.py --auto >> $LOG_FILE 2>&1

# Check if successful
if [ $? -eq 0 ]; then
    echo "Backup completed successfully at $(date)" >> $LOG_FILE
else
    echo "Backup FAILED at $(date)" >> $LOG_FILE
    # Send alert (customize as needed)
    # mail -s "Dolores Backup Failed" jon@example.com < $LOG_FILE
fi

# Keep only last 30 days of logs
find ./backup_logs -name "dolores_backup_*.log" -mtime +30 -delete
EOF

chmod +x dolores_daily_backup.sh

echo "✅ Created dolores_daily_backup.sh"

# Setup cron job
echo ""
echo "📅 To enable automated daily backups, add this to your crontab:"
echo "   crontab -e"
echo ""
echo "Add this line for daily backup at 2 AM:"
echo "0 2 * * * /home/jonclaude/agents/Hinkey/dolores_daily_backup.sh"
echo ""
echo "Or for hourly backups during work hours:"
echo "0 9-17 * * * /home/jonclaude/agents/Hinkey/dolores_daily_backup.sh"
echo ""

# Create systemd service alternative
cat > dolores-backup.service << EOF
[Unit]
Description=Dolores Knowledge Backup to Synology
After=network.target

[Service]
Type=oneshot
ExecStart=/home/jonclaude/agents/Hinkey/dolores_daily_backup.sh
User=jonclaude

[Install]
WantedBy=multi-user.target
EOF

cat > dolores-backup.timer << EOF
[Unit]
Description=Daily Dolores Backup Timer
Requires=dolores-backup.service

[Timer]
OnCalendar=daily
OnCalendar=*-*-* 02:00:00
Persistent=true

[Install]
WantedBy=timers.target
EOF

echo "🔄 Alternative: SystemD timer created"
echo "To enable:"
echo "  sudo cp dolores-backup.* /etc/systemd/system/"
echo "  sudo systemctl daemon-reload"
echo "  sudo systemctl enable dolores-backup.timer"
echo "  sudo systemctl start dolores-backup.timer"