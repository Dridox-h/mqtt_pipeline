#!/bin/sh
# git_pusher.sh — Commit & push automatique de events.json toutes les 30 secondes

echo "[git-pusher] 🚀 Démarrage..."

# ─── Config Git globale ───────────────────────────────────────────────────────
git config --global user.email "bot@mqtt-pipeline.local"
git config --global user.name "MQTT Pipeline Bot"
git config --global --add safe.directory /repo
git config --global core.autocrlf false

# ─── Injecter le token dans la remote URL ─────────────────────────────────────
REMOTE_URL="https://bot:${GITHUB_TOKEN}@github.com/${GITHUB_REPO}.git"
git -C /repo remote set-url origin "$REMOTE_URL"
echo "[git-pusher] 🔗 Remote : https://***@github.com/${GITHUB_REPO}.git"

# ─── Attente initiale (laisser le subscriber créer events.json) ───────────────
echo "[git-pusher] ⏳ Attente 20 s avant le premier cycle..."
sleep 20

# ─── Boucle principale ────────────────────────────────────────────────────────
while true; do
    cd /repo

    # Vérifier que le fichier existe
    if [ ! -f "data/events.json" ]; then
        echo "[$(date '+%H:%M:%S')] ⏳ data/events.json absent — retry dans 10 s..."
        sleep 10
        continue
    fi

    # Stager le fichier
    git add data/events.json

    # Rien à committer ?
    if git diff --cached --quiet; then
        echo "[$(date '+%H:%M:%S')] 💤 Aucun changement — skip."
    else
        # Compter les événements (grep shell-pur, sans python)
        COUNT=$(grep -c '"camera"' data/events.json 2>/dev/null || echo "?")

        git commit -m "chore: update events [auto] — ${COUNT} events"
        BRANCH=$(git rev-parse --abbrev-ref HEAD 2>/dev/null)
        if [ -z "$BRANCH" ] || [ "$BRANCH" = "HEAD" ]; then
            BRANCH="main"
        fi

        # Push (avec pull --rebase en cas de conflit)
        if git push origin "$BRANCH"; then
            echo "[$(date '+%H:%M:%S')] ✅ Push OK — ${COUNT} events — branche ${BRANCH}"
        else
            echo "[$(date '+%H:%M:%S')] ⚠️  Push rejeté — tentative pull --rebase..."
            git pull --rebase origin "$BRANCH" && git push origin "$BRANCH" \
                && echo "[$(date '+%H:%M:%S')] ✅ Push OK après rebase" \
                || { echo "[$(date '+%H:%M:%S')] ❌ Échec — reset du commit"; git reset HEAD~1; }
        fi
    fi

    sleep 30
done
