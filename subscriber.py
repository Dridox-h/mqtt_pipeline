import paho.mqtt.client as mqtt
import json
import os

# ─── Configuration ────────────────────────────────────────────────────────────
BROKER    = os.getenv("MQTT_BROKER", "127.0.0.1")
PORT      = 1883
TOPIC     = "camera/events"
DATA_FILE = "/data/events.json"   # Monté via volume ./data:/data
MAX_EVENTS = 100

# ─── Persistance JSON ─────────────────────────────────────────────────────────
def save_event(payload: dict) -> None:
    """Sauvegarde l'événement dans events.json (rolling window MAX_EVENTS)."""
    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)

    # Charger l'historique existant
    events = []
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                events = json.load(f)
        except (json.JSONDecodeError, IOError):
            events = []

    # Ajouter et tronquer
    events.append(payload)
    if len(events) > MAX_EVENTS:
        events = events[-MAX_EVENTS:]

    # Écriture atomique
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(events, f, indent=2, ensure_ascii=False)

# ─── Callbacks MQTT ───────────────────────────────────────────────────────────
def on_connect(client, userdata, flags, reason_code, properties):
    if reason_code == 0:
        print("✅ Subscriber connecté au broker MQTT !\n")
        client.subscribe(TOPIC)
        print(f"📡 En écoute sur '{TOPIC}' — stockage dans {DATA_FILE}\n")
        print("─" * 52)
    else:
        print(f"❌ Connexion refusée, code : {reason_code}")

def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode("utf-8"))

        # Affichage console
        print(f"🚨 [ÉVÉNEMENT] {payload.get('ts')}")
        print(f" ├─ Caméra    : {payload.get('camera')}")
        print(f" ├─ Événement : {payload.get('event')}")
        print(f" ├─ Zone      : {payload.get('zone')}")
        print(f" └─ Confiance : {payload.get('confidence', 0) * 100:.1f} %\n")
        print("─" * 52)

        # Persistance JSON
        save_event(payload)

    except json.JSONDecodeError:
        print(f"[BRUT] {msg.topic} → {msg.payload.decode('utf-8')}")

# ─── Client MQTT ──────────────────────────────────────────────────────────────
client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, "CameraSubscriber")
client.on_connect = on_connect
client.on_message = on_message

try:
    client.connect(BROKER, PORT, 60)
except Exception as e:
    print(f"❌ Erreur de connexion : {e}")
    exit(1)

try:
    client.loop_forever()
except KeyboardInterrupt:
    print("\n🛑 Subscriber arrêté.")
    client.disconnect()
