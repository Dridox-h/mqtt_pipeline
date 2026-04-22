import paho.mqtt.client as mqtt
import json
import os

# ─── Configuration MQTT ────────────────────────────────────────────────────────
BROKER     = os.getenv("MQTT_BROKER",    "127.0.0.1")
PORT       = 1883
TOPIC      = "camera/events"
DATA_FILE  = "/data/events.json"
MAX_EVENTS = 100

# ─── Configuration InfluxDB ───────────────────────────────────────────────────
INFLUXDB_URL    = os.getenv("INFLUXDB_URL",    "http://influxdb:8086")
INFLUXDB_TOKEN  = os.getenv("INFLUXDB_TOKEN",  "")
INFLUXDB_ORG    = os.getenv("INFLUXDB_ORG",    "mqtt_org")
INFLUXDB_BUCKET = os.getenv("INFLUXDB_BUCKET", "camera_events")

# ─── Client InfluxDB (non-bloquant si indisponible) ───────────────────────────
_influx_write_api = None
try:
    from influxdb_client import InfluxDBClient
    from influxdb_client.client.write_api import SYNCHRONOUS
    _influx_client   = InfluxDBClient(
        url=INFLUXDB_URL, token=INFLUXDB_TOKEN, org=INFLUXDB_ORG
    )
    _influx_write_api = _influx_client.write_api(write_options=SYNCHRONOUS)
    print(f"[InfluxDB] ✅ Client initialisé → {INFLUXDB_URL}")
except Exception as exc:
    print(f"[InfluxDB] ⚠️  Client non initialisé : {exc}")

# ─── Persistance JSON ─────────────────────────────────────────────────────────
def save_event(payload: dict) -> None:
    """Sauvegarde l'événement dans events.json (rolling window MAX_EVENTS)."""
    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
    events = []
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                events = json.load(f)
        except (json.JSONDecodeError, IOError):
            events = []
    events.append(payload)
    if len(events) > MAX_EVENTS:
        events = events[-MAX_EVENTS:]
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(events, f, indent=2, ensure_ascii=False)

# ─── Écriture InfluxDB ────────────────────────────────────────────────────────
def write_to_influx(payload: dict) -> None:
    """Écrit un Point dans InfluxDB 2.x — silencieux si InfluxDB est absent."""
    if _influx_write_api is None:
        return
    try:
        from influxdb_client import Point
        point = (
            Point("camera_events")
            .tag("camera", payload.get("camera", "unknown"))
            .tag("event",  payload.get("event",  "unknown"))
            .tag("zone",   payload.get("zone",   "unknown"))
            .field("confidence", float(payload.get("confidence", 0.0)))
            .time(payload.get("ts"))
        )
        _influx_write_api.write(
            bucket=INFLUXDB_BUCKET, org=INFLUXDB_ORG, record=point
        )
        print(
            f"[InfluxDB] ✅ Point écrit — "
            f"{payload.get('camera')} / {payload.get('event')}"
        )
    except Exception as exc:
        print(f"[InfluxDB] ⚠️  Erreur écriture : {exc}")

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

        print(f"🚨 [ÉVÉNEMENT] {payload.get('ts')}")
        print(f" ├─ Caméra    : {payload.get('camera')}")
        print(f" ├─ Événement : {payload.get('event')}")
        print(f" ├─ Zone      : {payload.get('zone')}")
        print(f" └─ Confiance : {payload.get('confidence', 0) * 100:.1f} %\n")
        print("─" * 52)

        save_event(payload)
        write_to_influx(payload)

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
