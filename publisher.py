import paho.mqtt.client as mqtt
import time
import json
import random
import os
from datetime import datetime, timezone

# ─── Configuration ────────────────────────────────────────────────────────────
BROKER = os.getenv("MQTT_BROKER", "127.0.0.1")
PORT   = 1883
TOPIC  = "camera/events"

# ─── Données simulées ─────────────────────────────────────────────────────────
CAMERAS = ["cam-1", "cam-2", "cam-3", "cam-4", "cam-garage"]
EVENTS  = ["motion", "person", "vehicle", "tamper", "offline"]
ZONES   = ["A", "B", "C", "entry", "parking"]

# ─── Callback connexion ───────────────────────────────────────────────────────
def on_connect(client, userdata, flags, reason_code, properties):
    if reason_code == 0:
        print("✅ Publisher connecté au broker MQTT !")
    else:
        print(f"❌ Connexion refusée, code : {reason_code}")

# ─── Client MQTT ──────────────────────────────────────────────────────────────
client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, "CameraPublisher")
client.on_connect = on_connect

try:
    client.connect(BROKER, PORT, 60)
except Exception as e:
    print(f"❌ Erreur de connexion : {e}")
    exit(1)

client.loop_start()
print("📤 Début de la publication (intervalle : 5 s)...\n")

# ─── Boucle de publication ────────────────────────────────────────────────────
try:
    while True:
        payload = {
            "camera":     random.choice(CAMERAS),
            "event":      random.choice(EVENTS),
            "zone":       random.choice(ZONES),
            "confidence": round(random.uniform(0.60, 0.99), 2),
            "ts":         datetime.now(timezone.utc).isoformat(timespec="seconds"),
        }
        message = json.dumps(payload)
        client.publish(TOPIC, message)
        print(f"📡 Publié → {message}")
        time.sleep(5)
except KeyboardInterrupt:
    print("\n🛑 Publisher arrêté.")
finally:
    client.loop_stop()
    client.disconnect()
