import copy
import datetime
import os
import sys
import uuid

import torch.multiprocessing as mp
import wandb
import yaml

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.GlobalVarGetter import GlobalVarGetter
from core.MessageQueue import MessageQueueFactory
from core.Runtime import running_mode
from utils.Tools import *
from utils import ModuleFindTool
import argparse


def generate_client_stale_list(global_config):
    stale = global_config['stale']
    if isinstance(stale, list):
        client_staleness_list = stale
    elif isinstance(stale, bool):
        client_staleness_list = []
        for i in range(global_config["client_num"]):
            client_staleness_list.append(0)
    elif isinstance(stale, dict) and "path" in stale:
        stale_generator = ModuleFindTool.find_class_by_path(stale["path"])()(stale["params"])
        client_staleness_list = stale_generator.generate_staleness_list()
    else:
        total_sum = sum(stale['list'])
        if total_sum < global_config['client_num']:
            raise Exception("The sum of the client number in stale list must not be less than the client number.")
        client_staleness_list = generate_stale_list(stale['step'], stale['shuffle'], stale['list'])
    return client_staleness_list


def main():
    parser = argparse.ArgumentParser(description='FedModule Framework')
    parser.add_argument('config_file', nargs='?', default='', help='config file path')
    parser.add_argument('--config', type=str, default='', help='config file path')
    parser.add_argument('--uid', type=str, default='', help='process uid to distinguish different runs')
    args = parser.parse_args()

    if not os.path.exists(os.path.join(os.path.dirname(os.path.abspath(__file__)), "../results")):
        os.mkdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), "../results"))

    config_file = args.config_file if args.config_file else args.config
    if config_file == '':
        config_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../config.json")
    config = None
    if config_file.endswith('.yaml') or config_file.endswith('.yml'):
        with open(config_file, 'r') as f:
            config = yaml.safe_load(f)
    elif config_file.endswith('.json'):
        config = getJson(config_file)
    else:
        yaml_path = os.path.splitext(config_file)[0] + '.yaml'
        json_path = os.path.splitext(config_file)[0] + '.json'
        if os.path.exists(yaml_path):
            with open(yaml_path, 'r') as f:
                config = yaml.safe_load(f)
        elif os.path.exists(json_path):
            config = getJson(json_path)
        else:
            raise FileNotFoundError(f"Configuration file {config_file} does not exist")

    uid = args.uid
    if uid == '':
        uuid_v4 = uuid.uuid4()
        uid = uuid_v4.hex
    config["global"]["uid"] = uid
    print("Global UID:", uid)

    if "seed" not in config["global"]:
        seed = generate_random_seed()
        config["global"]["seed"] = seed
    else:
        seed = config["global"]["seed"]
    random_seed_set(seed)
    print("Global seed:", seed)

    raw_config = copy.deepcopy(config)
    global_config = config['global']
    server_config = config['server']
    client_config = config['client']
    client_manager_config = config['client_manager']
    queue_manager_config = config['queue_manager']
    wandb_config = config['wandb']
    client_config["seed"] = seed

    if not global_config["experiment"].endswith("/"):
        global_config["experiment"] = global_config["experiment"] + "/"
    if not os.path.exists(
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "../results/", global_config["experiment"])):
        os.makedirs(
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "../results/", global_config["experiment"]))

    if "save" in global_config and not global_config["save"]:
        is_cover = False
    else:
        is_cover = True

    if os.path.exists(
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "../results/", global_config["experiment"],
                         "config.json")) and is_cover:
        is_cover = input("The experiment path already exists. Overwrite? (y/n): ")
        if is_cover == 'y' or is_cover == 'Y':
            is_cover = True
        else:
            print("Experiment results will not be saved.")
            is_cover = False
    global_config["save"] = is_cover

    if wandb_config["enabled"]:
        params = {}
        if "params" in wandb_config:
            params = wandb_config["params"]
        wandb.init(
            project=wandb_config["project"],
            config=config,
            name=wandb_config["name"],
            **params
        )

    GlobalVarGetter.set({'config': config, 'global_config': global_config,
                         'server_config': server_config,
                         'client_config': client_config,
                         'client_manager_config': client_manager_config,
                         'queue_manager_config': queue_manager_config})
    global_var = GlobalVarGetter.get()
    message_queue = MessageQueueFactory.create_message_queue(True)
    message_queue.set_config(global_var)

    start_time = datetime.datetime.now()

    if 'use_file_system' in global_config and global_config['use_file_system']:
        torch.multiprocessing.set_sharing_strategy('file_system')

    client_staleness_list = generate_client_stale_list(global_config)
    client_manager_config["stale_list"] = client_staleness_list
    global_var['client_staleness_list'] = client_staleness_list

    dataset_class = ModuleFindTool.find_class_by_path(global_config["dataset"]["path"])
    dataset = dataset_class(global_config["client_num"], global_config["iid"], global_config["dataset"]["params"])
    train_dataset = dataset.get_train_dataset()
    test_dataset = dataset.get_test_dataset()
    train_dataset, test_dataset = send_dataset(train_dataset, test_dataset, message_queue, global_config)
    index_list = dataset.get_index_list()
    test_index_list = dataset.get_test_index_list()
    client_manager_config["index_list"] = index_list
    global_var['client_index_list'] = index_list
    global_var['test_index_list'] = test_index_list

    if "data_proxy" in config:
        dp_conf = config["data_proxy"]
        DataProxyClass = ModuleFindTool.find_class_by_path(dp_conf["path"])
        data_proxy = DataProxyClass(**dp_conf.get("params", {}))
        GlobalVarGetter.set({"data_proxy": data_proxy})

    running_mode(config, output=True)
    client_manager_class = ModuleFindTool.find_class_by_path(client_manager_config["path"])
    client_manager = client_manager_class(config)
    client_manager.start_all_clients()

    server_config['updater']['enabled'] = wandb_config['enabled']
    server_class = ModuleFindTool.find_class_by_path(server_config["path"])
    server = server_class(config)
    server.run()

    client_manager.stop_all_clients()
    client_manager.client_join()

    del server

    print("Time used:")
    end_time = datetime.datetime.now()
    print(end_time - start_time)
    print(((end_time - start_time).seconds / 60), "min")
    print(((end_time - start_time).seconds / 3600), "h")

    if is_cover:
        raw_config['global']['stale'] = client_staleness_list
        saveJson(os.path.join(os.path.dirname(os.path.abspath(__file__)), "../results/", global_config["experiment"],
                              "config.json"), raw_config)
        saveAns(os.path.join(os.path.dirname(os.path.abspath(__file__)), "../results/", global_config["experiment"],
                             "time.txt"), end_time - start_time)
        result_to_markdown(
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "../results/", global_config["experiment"],
                         "Experiment_Description.md"), config)
    if wandb_config['enabled']:
        saveAns(os.path.join(wandb.run.dir, "time.txt"), end_time - start_time)
        saveJson(os.path.join(wandb.run.dir, "config.json"), raw_config)
        result_to_markdown(os.path.join(wandb.run.dir, "Experiment_Description.md"), config)


def cleanup():
    print()
    print("=" * 20)
    print("Starting cache cleanup...")
    print("Cache cleanup completed.")
    print("=" * 20)


if __name__ == '__main__':
    try:
        mp.set_start_method('spawn', force=True)
        main()
    finally:
        cleanup()
        MessageQueueFactory.del_message_queue()