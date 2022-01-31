import tensorflow as tf
import torch
import json
import subprocess

output = {'torch':False, 'tensorflow': False, 'msg':'' }

try:
    output['tensorflow'] = len(tf.config.list_physical_devices('GPU')) > 0
except Exception as ex:
    output['msg'] += str(ex) + " "
# nvidia-smi is added during initContainer
# proc = subprocess.run(["nvidia-smi"], capture_output=True)
# output['cuda'] = str(proc.stdout)
try:
    output['torch'] = torch.cuda.is_available()
except Exception as ex:
    output['msg'] += str(ex)
out = json.dumps(output,indent=2)

print(out)
