try:
    import tensorflow as tf
    import torch
    import json
    from functools import wraps
    import numpy as np
    from tensorflow.keras.models import Model
    from tensorflow.keras.layers import Dense, Input

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
    # check GPUs
    log['tensorflow'] = len(tf.config.list_physical_devices('GPU')) > 0
    
    # random job
    try:
        X = np.random.random((100, 16))
        y = np.random.randint(0, 2, size=(100,))
        tf.config.set_visible_devices(gpus[0], 'GPU')
        inputs = Input(shape=X.shape[1:])
        x = Dense(4, activation="tanh")(inputs)
        outputs = Dense(1, activation='sigmoid')(x)
        model = Model(inputs=inputs, outputs=outputs)
        model.compile(optimizer="sgd", loss="binary_crossentropy")

        model.fit(X, y, verbose=1, epochs=1, batch_size=1)
    
    except Exception as e:
        print(f'Tensorflow exception {e}')
        return False

@log_errors
def is_torch_available(log):
    log['torch'] = torch.cuda.is_available()


if __name__ == '__main__':
    log = {'torch':False, 'tensorflow': False, 'msg':'' }
    is_tensorflow_available(log)
    is_torch_available(log)
    print(json.dumps(log,indent=2))