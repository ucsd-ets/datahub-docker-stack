import tensorflow as tf
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error
import numpy as np


def get_GPU_context():
    # Check if GPU is available
    if tf.config.list_physical_devices('GPU'):
        device = '/GPU:0'

        # Prevent TF from using all available NVRAM...
        gpus = tf.config.list_physical_devices('GPU')
#         for gpu in gpus:
#             tf.config.experimental.set_memory_growth(gpu, True)
    else:
        raise Exception("Test failed, TensorFlow could not detect GPU.")

    return tf.device(device)


def run_SLR_model():

    # Set fixed seed for tf and np
    np.random.seed(12345)
    tf.random.set_seed(12345)

    # Generate some sample data for linear regression
    X = np.random.rand(100, 1)
    y = 2 * X + 1 + 0.1 * np.random.randn(100, 1)

    # Split the data into training and test sets
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42)

    with get_GPU_context():
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


def multiply_matrices():

    # Perform a simple matrix multiplication on the GPU
    with get_GPU_context():
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


def test_run_find_GPUs():
    gpu = get_GPU_context()
    assert gpu != None


def test_run_SLR_model():
    result = run_SLR_model()
    assert result == "Test succeeded"


def test_multiply_matrices():
    result = multiply_matrices()
    assert result == "Test Succeeded"


def test_arithmetic():
    # Define the TensorFlow graph
    a = tf.constant(2.0, dtype=tf.float32)
    b = tf.constant(3.0, dtype=tf.float32)
    c = tf.constant(1.0, dtype=tf.float32)
    result = tf.add(tf.multiply(a, b), c)

    # Execute the graph using eager execution
    output = result.numpy()

    assert output == 7.0
