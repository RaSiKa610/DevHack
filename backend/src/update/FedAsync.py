import torch
import numpy as np

from update.AbstractUpdate import AbstractUpdate
from utils.GlobalVarGetter import GlobalVarGetter


class FedAsync(AbstractUpdate):
    def __init__(self, config):
        self.config = config
        self.global_var = GlobalVarGetter.get()

        self.distance_history = []
        self.trust_scores = {}   # 🔥 NEW: trust score tracking

        self.hetero_threshold = config.get("hetero_threshold", 5.0)
        self.hetero_penalty = config.get("hetero_penalty", 0.5)

        self.trust_decay = config.get("trust_decay", 0.2)
        self.trust_boost = config.get("trust_boost", 0.05)

    def compute_distance(self, client_weights, server_weights):
        total_norm = 0.0
        for key in server_weights.keys():
            diff = client_weights[key] - server_weights[key]
            total_norm += torch.norm(diff).item()
        return total_norm

    def is_malicious(self, distance):
        if len(self.distance_history) < 5:
            return False

        mean = np.mean(self.distance_history)
        std = np.std(self.distance_history)

        if std == 0:
            return False

        z_score = (distance - mean) / std

        print(f"Distance: {distance:.4f}, Mean: {mean:.4f}, Std: {std:.4f}, Z-score: {z_score:.4f}")

        if abs(z_score) > 2.5:
            print("🚨 Malicious update detected via Z-score anomaly detection!")
            return True

        return False

    def update_server_weights(self, epoch, update_list):
        update_dict = update_list[0]
        client_weights = update_dict["weights"]
        time_stamp = update_dict["time_stamp"]
        client_id = update_dict["client_id"]

        b = self.config["b"]
        a = self.config["a"]
        alpha = self.config["alpha"]
        r = self.config["r"]

        server_weights = self.global_var['updater'].model.state_dict()

        # -------------------------
        # INITIALIZE TRUST IF NEW
        # -------------------------
        if client_id not in self.trust_scores:
            self.trust_scores[client_id] = 1.0

        # -------------------------
        # DISTANCE
        # -------------------------
        distance = self.compute_distance(client_weights, server_weights)

        # -------------------------
        # MALICIOUS CHECK
        # -------------------------
        if self.is_malicious(distance):
            print(f"⚠ Update rejected from client {client_id}")
            self.trust_scores[client_id] -= self.trust_decay
            self.trust_scores[client_id] = max(self.trust_scores[client_id], 0.1)
            return server_weights, None

        self.distance_history.append(distance)

        # -------------------------
        # TRUST BOOST (GOOD UPDATE)
        # -------------------------
        self.trust_scores[client_id] += self.trust_boost
        self.trust_scores[client_id] = min(self.trust_scores[client_id], 1.5)

        print(f"Client {client_id} trust score: {self.trust_scores[client_id]:.2f}")

        # -------------------------
        # HETEROGENEITY PENALTY
        # -------------------------
        if distance > self.hetero_threshold:
            print("⚠ High divergence detected — soft penalization applied.")
            alpha *= self.hetero_penalty

        # -------------------------
        # STALENESS
        # -------------------------
        current_time = self.global_var['updater'].current_t.get_time()

        if (current_time - time_stamp) <= b:
            s = 1
        else:
            s = float(1 / ((a * (current_time - time_stamp - b)) + 1))

        alpha = alpha * s * r

        # -------------------------
        # APPLY TRUST SCALING
        # -------------------------
        alpha *= self.trust_scores[client_id]

        updated_parameters = {}

        for key in server_weights.keys():
            updated_parameters[key] = (
                alpha * client_weights[key] +
                (1 - alpha) * server_weights[key]
            )

        print("Robust aggregation (Z-score + Trust + Heterogeneity-aware) applied.")

        return updated_parameters, None