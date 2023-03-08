try:
    import tensorflow as tf
    import torch
    import json
    from functools import wraps
except Exception as ex:
    print(f'Image missing a necessary package: {ex}')
    quit()
def log_errors(f):
    @wraps(f)
    def inner_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as ex:
            args[0]['msg'] = str(ex)
    return inner_function

@log_errors
def is_tensorflow_available(log):
    log['tensorflow'] = len(tf.config.list_physical_devices('GPU')) > 0

@log_errors
def is_torch_available(log):
    log['torch'] = torch.cuda.is_available()


if __name__ == '__main__':
    log = {'torch':False, 'tensorflow': False, 'msg':'' }
    is_tensorflow_available(log)
    is_torch_available(log)
    print(json.dumps(log,indent=2))