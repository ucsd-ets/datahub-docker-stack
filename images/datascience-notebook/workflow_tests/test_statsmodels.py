import numpy as np
import statsmodels.api as sm
import pytest

def test_ols_simple_fit():
    # Generate synthetic data (reproducible with seed(0))
    np.random.seed(0)
    X = np.random.rand(100, 1)
    X = sm.add_constant(X)  # Adds a constant term for the intercept
    beta = [0.5, 2.0]  # True coefficients
    y = np.dot(X, beta) + np.random.normal(size=100)
    
    # Fit the model
    model = sm.OLS(y, X)
    results = model.fit()
    
    # Check if the estimated coefficients are close to the true coefficients
    assert np.allclose(results.params, beta, atol=0.5), "The estimated coefficients are not as expected."

def test_logistic_regression_prediction():
    # Generate synthetic data
    np.random.seed(1)
    X = np.random.randn(100, 2)
    X = sm.add_constant(X)
    beta = [0.1, 0.5, -0.3]
    y_prob = 1 / (1 + np.exp(-np.dot(X, beta)))  # Sigmoid function for true probabilities
    y = (y_prob > 0.5).astype(int)  # Binary outcome
    
    # Fit the logistic regression model
    model = sm.Logit(y, X)
    results = model.fit(disp=0)  # disp=0 suppresses the optimization output
    
    # Predict using the model
    predictions = results.predict(X) > 0.5
    
    # Check if the predictions match the actual binary outcomes
    accuracy = np.mean(predictions == y)
    assert accuracy > 0.75, "The prediction accuracy should be higher than 75%."

def test_ols_summary_contains_r_squared():
    # Simple linear regression with synthetic data
    np.random.seed(2)
    X = np.random.rand(50, 1)
    y = 2 * X.squeeze() + 1 + np.random.normal(scale=0.5, size=50)
    X = sm.add_constant(X)
    
    model = sm.OLS(y, X)
    results = model.fit()
    
    summary_str = str(results.summary())
    
    # Check if 'R-squared' is in the summary
    assert 'R-squared' in summary_str, "'R-squared' not found in the model summary."
