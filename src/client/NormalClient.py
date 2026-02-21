from client.Client import Client
from client.mixin.ClientHandler import UpdateReceiver, DelaySimulator, UpdateSender
from client.mixin.InitHandler import InitHandler
from core.handlers.Handler import HandlerChain
from core.handlers.ModelTrainHandler import ClientTrainHandler, ClientPostTrainHandler
from client.mixin.DataStore import DataStore
import torch


class NormalClient(Client):

    def __init__(self, c_id, stop_event, selected_event, delay, index_list, config, dev, data_proxy=None):
        super().__init__(c_id, stop_event, selected_event, delay, index_list, dev)
        self.init_chain = HandlerChain()
        self.update_dict = {}
        self.lr_scheduler = None
        self.batch_size = config.get("batch_size", 64)
        self.epoch = config["epochs"]
        self.optimizer_config = config["optimizer"]
        self.mu = config.get("mu", 0)
        self.config = config
        self.data_proxy = data_proxy if data_proxy is not None else DataStore()

    @property
    def fl_train_ds(self):
        return self.data_proxy.get(self.client_id, 'fl_train_ds')

    @fl_train_ds.setter
    def fl_train_ds(self, value):
        self.data_proxy.set(self.client_id, 'fl_train_ds', value)

    @property
    def optimizer(self):
        return self.data_proxy.get(self.client_id, 'optimizer')

    @optimizer.setter
    def optimizer(self, value):
        self.data_proxy.set(self.client_id, 'optimizer', value)

    @property
    def loss_func(self):
        return self.data_proxy.get(self.client_id, 'loss_func')

    @loss_func.setter
    def loss_func(self, value):
        self.data_proxy.set(self.client_id, 'loss_func', value)

    @property
    def train_dl(self):
        return self.data_proxy.get(self.client_id, 'train_dl')

    @train_dl.setter
    def train_dl(self, value):
        self.data_proxy.set(self.client_id, 'train_dl', value)

    def _run_iteration(self):
        while not self.stop_event.is_set():
            if self.event.is_set():
                self.event.clear()
                self.local_run()
            else:
                self.event.wait()

    def local_run(self):
        self.message_queue.set_training_status(self.client_id, True)
        self.execute_chain()
        self.message_queue.set_training_status(self.client_id, False)

    def execute_chain(self):
        request = {"global_var": self.global_var, "client": self, 'epoch': self.time_stamp}
        self.handler_chain.handle(request)

    def init(self):
        request = {"global_var": self.global_var, "client": self, "config": self.config}
        self.init_chain.handle(request)

    def receive_notify(self):
        pass

    def create_handler_chain(self):
        self.init_chain = HandlerChain(InitHandler())
        self.handler_chain = HandlerChain()
        (self.handler_chain.set_chain(UpdateReceiver())
         .set_next(ClientTrainHandler())
         .set_next(ClientPostTrainHandler())
         .set_next(DelaySimulator())
         .set_next(UpdateSender()))

    def finish(self):
        pass

    def upload(self, **kwargs):
        self.update_dict["client_id"] = self.client_id
        self.update_dict["time_stamp"] = self.time_stamp

        for k, v in kwargs.items():
            self.upload_item(k, v)

        # ==============================
        # 🔐 Differential Privacy Layer
        # ==============================

        sigma = self.config.get("dp_sigma", 0.0)
        clip_value = self.config.get("dp_clip", None)

        if sigma > 0 and "weights" in self.update_dict:
            for key in self.update_dict["weights"]:
                tensor = self.update_dict["weights"][key]

                # L2 norm clipping
                if clip_value is not None:
                    norm = torch.norm(tensor)
                    if norm > clip_value:
                        tensor = tensor * (clip_value / norm)

                # Gaussian noise injection
                noise = torch.normal(
                    mean=0.0,
                    std=sigma,
                    size=tensor.shape,
                    device=tensor.device
                )

                tensor = tensor + noise
                self.update_dict["weights"][key] = tensor

        # ====================================
        # 🚨 Malicious Simulation (Testing)
        # ====================================

        if self.client_id == 0:
            if "weights" in self.update_dict:
                print("🚨 Malicious client 0 activated — heavily corrupting weights!")
                corrupted = {}
                for key in self.update_dict["weights"]:
                    corrupted[key] = self.update_dict["weights"][key] * 100
                self.update_dict["weights"] = corrupted

        self.customize_upload()
        self.message_queue.put_into_uplink(self.update_dict)
        print("Client", self.client_id, "uploaded")

    def upload_item(self, k, v):
        self.update_dict[k] = v

    def customize_upload(self):
        pass

    def run_one_iteration(self, client_dict=None):
        if client_dict is not None:
            for k, v in client_dict.items():
                setattr(self, k, v)

        self.message_queue.set_training_status(self.client_id, True)
        self.execute_chain()
        self.message_queue.set_training_status(self.client_id, False)

        return self


class NormalClientWithDelta(NormalClient):
    def __init__(self, c_id, stop_event, selected_event, delay, index_list, config, dev):
        super().__init__(c_id, stop_event, selected_event, delay, index_list, config, dev)
        self.config['train_func'] = 'core.handlers.ModelTrainHandler.TrainWithDelta'


class NormalClientWithGrad(NormalClient):
    def __init__(self, c_id, stop_event, selected_event, delay, index_list, config, dev):
        super().__init__(c_id, stop_event, selected_event, delay, index_list, config, dev)
        self.config['train_func'] = 'core.handlers.ModelTrainHandler.TrainWithGrad'