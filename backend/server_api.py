from flask import Flask, jsonify
from flask_cors import CORS
from flask_socketio import SocketIO
import random
import threading
import time

app = Flask(__name__)
CORS(app)

# Enable WebSocket support
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading")

# ----------------------------
# Simulated Shared State
# ----------------------------

global_state = {
    "round": 0,
    "global_accuracy": 0.5,
    "global_loss": 1.0,
    "rejected_updates": 0,
    "dp_sigma": 0.05,
    "clip_norm": 1.0
}

clients = [
    {"id": 1, "trust": 0.92, "status": "active"},
    {"id": 2, "trust": 0.81, "status": "active"},
    {"id": 3, "trust": 0.45, "status": "malicious"}
]

logs = []


# ----------------------------
# Async Training Simulation
# ----------------------------

def simulate_training():
    while True:
        time.sleep(3)

        # Update global metrics
        global_state["round"] += 1
        global_state["global_accuracy"] += random.uniform(0.01, 0.03)
        global_state["global_loss"] -= random.uniform(0.02, 0.05)
        global_state["rejected_updates"] += random.randint(0, 1)

        # Simulate trust fluctuation
        for c in clients:
            change = random.uniform(-0.02, 0.02)
            c["trust"] = max(0, min(1, c["trust"] + change))

        # Add log entry
        logs.append(f"Round {global_state['round']} aggregation complete.")
        if len(logs) > 20:
            logs.pop(0)

        # Emit real-time updates
        socketio.emit("server_update", global_state)

        socketio.emit("clients_update", [
            {
                "id": c["id"],
                "trust": c["trust"],
                "status": c["status"],
                "staleness": random.randint(0, 5)
            }
            for c in clients
        ])

        socketio.emit("logs_update", logs)


# Start async thread
threading.Thread(target=simulate_training, daemon=True).start()

# Start async task using socketio
@socketio.on("connect")
def handle_connect():
    print("Client connected")
    socketio.start_background_task(simulate_training)


# ----------------------------
# REST API Endpoints (Fallback / Direct Fetch)
# ----------------------------

@app.route("/")
def home():
    return jsonify({"message": "Federated Learning WebSocket API Running"})


@app.route("/api/server/status")
def server_status():
    return jsonify(global_state)


@app.route("/api/clients")
def get_clients():
    return jsonify([
        {
            "id": c["id"],
            "trust": c["trust"],
            "status": c["status"],
            "staleness": random.randint(0, 5)
        }
        for c in clients
    ])


@app.route("/api/logs")
def get_logs():
    return jsonify(logs)


@app.route("/api/client/<int:client_id>")
def client_details(client_id):
    return jsonify({
        "id": client_id,
        "local_accuracy": random.uniform(0.6, 0.9),
        "trust": random.uniform(0.4, 0.95),
        "update_status": random.choice(["Accepted", "Rejected"]),
        "dp_sigma": global_state["dp_sigma"],
        "clip_norm": global_state["clip_norm"]
    })


# ----------------------------
# Run Server
# ----------------------------

if __name__ == "__main__":
    socketio.run(app, debug=True, port=5000)