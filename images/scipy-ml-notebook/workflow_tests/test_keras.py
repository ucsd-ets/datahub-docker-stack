import numpy as np
from keras.models import Sequential
from keras.layers import Dense
import pytest

@pytest.fixture
def simple_model():
    model = Sequential()
    model.add(Dense(units=10, activation='relu', input_shape=(5,)))
    model.add(Dense(units=1, activation='sigmoid'))
    model.compile(optimizer='adam', loss='binary_crossentropy', metrics=['accuracy'])
    return model

def test_model_training(simple_model):
    x_train = np.random.random((100, 5))
    y_train = np.random.randint(2, size=(100, 1))
    simple_model.fit(x_train, y_train, epochs=1, batch_size=32, verbose=0)
    assert simple_model.layers[0].input.shape == (None, 5)
    assert simple_model.layers[1].output.shape == (None, 1)

def test_model_evaluation(simple_model):
    x_test = np.random.random((20, 5))
    y_test = np.random.randint(2, size=(20, 1))
    loss, accuracy = simple_model.evaluate(x_test, y_test, verbose=0)
    assert loss >= 0
    assert 0 <= accuracy <= 1

def test_model_prediction(simple_model):
    x_new = np.random.random((1, 5))
    prediction = simple_model.predict(x_new)
    assert prediction.shape == (1, 1)
    assert 0 <= prediction <= 1