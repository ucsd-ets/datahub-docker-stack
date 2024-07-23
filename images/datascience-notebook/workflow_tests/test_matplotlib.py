import matplotlib.pyplot as plt
import numpy as np

def create_simple_plot(x, y, title="Test Plot"):
    fig, ax = plt.subplots()
    ax.plot(x, y)
    ax.set_title(title)
    return fig, ax

def test_number_of_plots_created():
    x = np.arange(0, 10, 1)
    y = x ** 2
    fig, ax = create_simple_plot(x, y)
    assert len(fig.axes) == 1, "There should be exactly one plot created"

def test_plot_title_is_correct():
    x = np.arange(0, 10, 1)
    y = x ** 2
    title = "Test Plot"
    _, ax = create_simple_plot(x, y, title=title)
    assert ax.get_title() == title, f"The title should be '{title}'"

def test_data_matches_input():
    x = np.arange(0, 10, 1)
    y = x ** 2
    _, ax = create_simple_plot(x, y)
    line = ax.lines[0]  # Get the first (and in this case, only) line object
    np.testing.assert_array_equal(line.get_xdata(), x, "X data does not match input")
    np.testing.assert_array_equal(line.get_ydata(), y, "Y data does not match input")