import tensorflow as tf
import torch
import json
import subprocess

output = {'torch':'null', 'tensorflow': 'null', 'cuda': 'null', 'msg':'null' }


output['tensorflow'] = len(tf.config.list_physical_devices('GPU')) > 0
subprocess.run(["nvidia-smi"],capture_output=True)
output['cuda'] = proc.stdout
output['torch'] = torch.cuda.is_available()
out = json.dumps(output,indent=2)

print(out)
