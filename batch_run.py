import yaml
import subprocess
import copy
import sys
import os

lr_list = [0.1, 0.01, 0.05]

with open('config.yaml', 'r') as f:
    base_config = yaml.safe_load(f)

for idx, lr in enumerate(lr_list, 1):
    config = copy.deepcopy(base_config)

    config['client']['optimizer']['params']['lr'] = lr
    config['wandb']['name'] = f"lr_{lr}"
    config['global']['experiment'] = f"FedAsync/lr_{lr}"

    config_path = f"config_lr_{lr}.yaml"

    with open(config_path, 'w') as f:
        yaml.dump(config, f, allow_unicode=True, sort_keys=False)

    subprocess.run([sys.executable, '-m', 'src.fl.main', config_path], cwd=os.path.dirname(os.path.abspath(__file__)))