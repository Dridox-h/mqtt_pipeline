# 📡 MQTT Camera Event Pipeline

Mini-pipeline complet de bout-en-bout : génération → transport MQTT → stockage JSON → push GitHub automatique.

## 🏗️ Architecture

```
publisher.py  ──MQTT──►  mosquitto  ──MQTT──►  subscriber.py
   (5 s)                  broker                  │
                                                  ▼
                                          data/events.json
                                                  │
                                          git-pusher (30 s)
                                                  │
                                                  ▼
                                           GitHub repo
```

| Service | Image / Base | Rôle |
|---|---|---|
| **mosquitto** | `eclipse-mosquitto` | Broker MQTT central |
| **publisher** | Python 3.9-slim | Génère des métadonnées caméra toutes les 5 s |
| **subscriber** | Python 3.9-slim | Reçoit et persiste dans `data/events.json` |
| **git-pusher** | `alpine/git` | Commit + push vers GitHub toutes les 30 s |

## 📦 Format des événements

```json
{
  "camera": "cam-3",
  "event": "motion",
  "zone": "A",
  "confidence": 0.87,
  "ts": "2026-04-22T00:00:00+00:00"
}
```

## 🚀 Lancement

### 1. Prérequis
- [Docker Desktop](https://docs.docker.com/get-docker/) installé et en cours d'exécution
- Accès internet (pull des images)

### 2. Configuration initiale (une seule fois)

```bash
# Initialiser le repo git et connecter au GitHub distant
git init

# Vérifier que .env est présent (déjà pré-rempli si vous avez cloné ce projet)
cat .env
```

### 3. Démarrer le pipeline

```bash
docker compose up -d
```

### 4. Suivre les événements en temps réel

```bash
# Logs subscriber (réception + sauvegarde JSON)
docker compose logs -f subscriber

# Logs git-pusher (commits automatiques)
docker compose logs -f git-pusher

# Tous les services
docker compose logs -f
```

### 5. Vérifier le fichier JSON en direct

```bash
# Windows PowerShell
Get-Content data\events.json | ConvertFrom-Json

# Ou simplement ouvrir data/events.json dans votre éditeur
```

### 6. Arrêter

```bash
docker compose down
```

## 📂 Structure du projet

```
mqtt_pipeline/
├── publisher.py        # Générateur d'événements (MQTT publisher)
├── subscriber.py       # Récepteur + persistance JSON
├── git_pusher.sh       # Script de push automatique GitHub
├── mosquitto.conf      # Config broker Mosquitto
├── Dockerfile          # Image Python pour publisher/subscriber
├── docker-compose.yaml # Orchestration des 4 services
├── requirements.txt    # paho-mqtt==2.1.0
├── .env                # Token GitHub (GITIGNORED — ne pas committer)
├── .env.example        # Template du .env
└── data/
    └── events.json     # Événements accumulés (rolling window 100)
```

## ⚙️ Variables d'environnement

| Variable | Valeur par défaut | Description |
|---|---|---|
| `MQTT_BROKER` | `mosquitto` | Hostname du broker dans Docker |
| `GITHUB_TOKEN` | _(depuis .env)_ | Personal Access Token GitHub (scope `repo`) |
| `GITHUB_REPO` | `Dridox-h/mqtt_pipeline` | Repo cible pour le push |

## 🔧 Personnalisation

- **Fréquence de publication** : modifier `time.sleep(5)` dans `publisher.py`
- **Fréquence de push** : modifier `sleep 30` dans `git_pusher.sh`
- **Rolling window** : modifier `MAX_EVENTS = 100` dans `subscriber.py`

## 🛠️ Technologies

- **Python 3.9** — Publisher & Subscriber
- **Paho-MQTT 2.1** — Client MQTT (API v2)
- **Eclipse Mosquitto** — Broker MQTT
- **Alpine/Git** — Service de push GitHub
- **Docker Compose** — Orchestration

---
*Pipeline auto-généré — events.json mis à jour automatiquement par le service git-pusher.*
