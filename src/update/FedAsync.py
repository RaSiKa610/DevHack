from update.AbstractUpdate import AbstractUpdate
from utils.GlobalVarGetter import GlobalVarGetter
import torch


class FedAsync(AbstractUpdate):
    def __init__(self, config):
        self.config = config
        self.global_var = GlobalVarGetter.get()

    def median_aggregation(self, weight_list):
        print("Robust aggregation (Median) is being applied...")
        aggregated = {}
        keys = weight_list[0].keys()

        for key in keys:
            stacked = torch.stack([w[key] for w in weight_list])
            aggregated[key] = torch.median(stacked, dim=0).values

        return aggregated

    def update_server_weights(self, epoch, update_list):
        server_weights = self.global_var['updater'].model.state_dict()

        client_weights_list = [u["weights"] for u in update_list]
        time_stamp = update_list[0]["time_stamp"]

        robust_client_weights = self.median_aggregation(client_weights_list)

        b = self.config["b"]
        a = self.config["a"]
        alpha = self.config["alpha"]
        r = self.config["r"]

        current_time = self.global_var['updater'].current_t.get_time()

        if (current_time - time_stamp) <= b:
            s = 1
        else:
            s = float(1 / ((a * (current_time - time_stamp - b)) + 1))

        alpha = alpha * s * r

        updated_parameters = {}

        for key in server_weights.keys():
            updated_parameters[key] = (
                alpha * robust_client_weights[key]
                + (1 - alpha) * server_weights[key]
            )

        print("Number of async updates received:", len(update_list))

        return updated_parameters, None