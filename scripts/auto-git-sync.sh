#!/bin/bash
# Auto-Commit & Push für Git-Repositories
# Sollte per Cron täglich laufen (z.B. 23:00 Uhr)

set -e

REPOS=(
    "/home/node/.openclaw/workspace/projects/personal-agent-rules"
    "/home/node/.openclaw/workspace/projects/csc-administration"
    # Weitere Repos hier hinzufügen
)

LOGFILE="/var/log/auto-git-sync.log"
DATE=$(date '+%Y-%m-%d %H:%M:%S')

echo "[$DATE] Starting auto-git-sync..." >> "$LOGFILE"

for REPO in "${REPOS[@]}"; do
    if [ -d "$REPO/.git" ]; then
        cd "$REPO"
        REPO_NAME=$(basename "$REPO")
        
        # Prüfe auf Änderungen
        if [ -n "$(git status --porcelain)" ]; then
            echo "[$DATE] Changes detected in $REPO_NAME" >> "$LOGFILE"
            
            # Alle Änderungen stagen
            git add -A
            
            # Commit mit Timestamp
            git commit -m "Auto-sync: $(date '+%Y-%m-%d %H:%M')" || true
            
            # Push (wird ohne Authentifizierung fehlschlagen, daher nur lokal commit)
            # Für Push brauchst du SSH-Keys oder Credentials
            if git push origin main 2>/dev/null; then
                echo "[$DATE] ✅ Pushed $REPO_NAME" >> "$LOGFILE"
            else
                echo "[$DATE] ⚠️  Local commit only (push failed) for $REPO_NAME" >> "$LOGFILE"
            fi
        else
            echo "[$DATE] No changes in $REPO_NAME" >> "$LOGFILE"
        fi
    fi
done

echo "[$DATE] Auto-git-sync completed" >> "$LOGFILE"