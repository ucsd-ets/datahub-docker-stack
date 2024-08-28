import tensorflow as tf
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error
import numpy as np
import pytest

@pytest.fixture(scope='session')
def gpu():
    # Check if GPU is available
    if tf.config.list_physical_devices('GPU'):
        device = '/GPU:0'

        # Prevent TF from using all available NVRAM...
        gpus = tf.config.list_physical_devices('GPU')
        
        # This prevents a GPU OOM crash with pytorch.
        # It does however "lock in" this experimental setting until the pod is restarted.
        #for gpu in gpus:
        #    tf.config.experimental.set_memory_growth(gpu, True)
    else:
        raise Exception("Test failed, TensorFlow could not detect GPU.")

    return tf.device(device)

def test_run_find_GPUs(gpu):
    assert gpu != None

def run_SLR_model(gpu):
    # Set fixed seed for tf and np
    np.random.seed(12345)
    tf.random.set_seed(12345)

    # Generate some sample data for linear regression
    X = np.random.rand(100, 1)
    y = 2 * X + 1 + 0.1 * np.random.randn(100, 1)

    # Split the data into training and test sets
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42)

    with gpu:
        # Create a simple linear regression modelLoaded cuDNN version 8600
        model = tf.keras.Sequential([
            tf.keras.layers.Dense(1, input_shape=(1,))
        ])

        # Compile the model
        model.compile(optimizer='adam', loss='mse')

        # Train the model
        model.fit(X_train, y_train, epochs=100, verbose=0)

    # Test the model and check the output
    try:
        y_pred = model.predict(X_test)
        mse = mean_squared_error(y_test, y_pred)
#         print(mse)

        if mse > 10:
            print("Test failed, inaccurate model generated")
            return
    except:
        print("Test failed, could not run model")
        return

    return ("Test succeeded")

def test_run_SLR_model(gpu):
    result = run_SLR_model(gpu)
    assert result == "Test succeeded"

def multiply_matrices(gpu):
    # Perform a simple matrix multiplication on the GPU
    with gpu:
        a = tf.constant([[1.0, 2.0], [3.0, 4.0]])
        b = tf.constant([[1.0, 1.0], [0.0, 1.0]])
        c = tf.matmul(a, b)

    expected = np.array([[1., 3.], [3., 7.]])

    if not np.array_equal(expected, c.numpy()):
        print("Test failed, wrong output")
        print("Output was: \n" + str(c.numpy()) +
              "\n Expected: \n" + str(expected))
        return
    return ("Test Succeeded")

def test_multiply_matrices(gpu):
    result = multiply_matrices(gpu)
    assert result == "Test Succeeded"

def test_arithmetic(gpu):
    with gpu:
        # Define the TensorFlow graph
        a = tf.constant(2.0, dtype=tf.float32)
        b = tf.constant(3.0, dtype=tf.float32)
        c = tf.constant(1.0, dtype=tf.float32)
        result = tf.add(tf.multiply(a, b), c)

        # Execute the graph using eager execution
        output = result.numpy()

        assert output == 7.0

def test_tensorrt(gpu):
    # Make sure tensorflow sees tensorRT

    import tensorflow.compiler as tf_cc
    linked_trt_ver=tf_cc.tf2tensorrt._pywrap_py_utils.get_linked_tensorrt_version()
    assert linked_trt_ver != "(0, 0, 0)", "TensorRT not recognized by tensorflow"

    loaded_trt_ver=tf_cc.tf2tensorrt._pywrap_py_utils.get_loaded_tensorrt_version()
    assert loaded_trt_ver != "(0, 0, 0)", "TensorRT not recognized by tensorflow"
    
    assert linked_trt_ver == loaded_trt_ver # If this is not true, tensorflow will crash

def test_cublas(gpu):
    with gpu:
        a = tf.random.uniform([1000, 1000], dtype=tf.float32)
        b = tf.random.uniform([1000, 1000], dtype=tf.float32)

        # Perform matrix multiplication
        c = tf.matmul(a, b)

        assert c.shape == (1000, 1000), "Matrix multiplication result shape mismatch"

def test_cudnn(gpu):
    with gpu:
        # Create a simple input tensor
        input_data = tf.random.normal([1, 28, 28, 3])  # Batch size 1, 28x28 image, 3 channels

        # Create a convolutional layer
        conv_layer = tf.keras.layers.Conv2D(filters=32, kernel_size=3, activation='relu')

        # Apply the convolutional layer to the input data
        output_data = conv_layer(input_data)

        # Check that the output has the expected shape
        assert output_data.shape == (1, 26, 26, 32), "Output shape is incorrect"

def test_cufft(gpu):
    with gpu:
        x = tf.random.uniform([1024], dtype=tf.float32)

        # Perform FFT
        fft_result = tf.signal.fft(tf.cast(tf.complex(x, tf.zeros_like(x)), tf.complex64))

        ifft_result = tf.signal.ifft(fft_result)

        # Ensure the inverse FFT returns to the original tensor
        assert np.allclose(x.numpy(), tf.math.real(ifft_result).numpy(), atol=1e-4), "Inverse FFT result mismatch"  