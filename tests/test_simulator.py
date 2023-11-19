import pytest
import simulator
import logging

from PyQt6 import QtCore


@pytest.fixture
def app(qtbot):
    """
    Main App;
    """
    test_app = simulator.MainWindow(logger=log())
    qtbot.addWidget(test_app)

    load_values(test_app)   # Changes variable values, not inputs of GUI.
    return test_app


def log():
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.NOTSET)     # Disabel logging, else test will print to console.
    return logger


def test_inputs(app):
    """
    Test inputs, Qedits
    """
    assert app.voltage_edit.text() == "5.0"

    # Set New values in load_values(), and setText like below.
    app.voltage_edit.setText(f"{app.voltage}")
    assert app.voltage_edit.text() == "10.0"

    # Frequency.
    assert app.freq_edit.text() == "10"
    assert app.freq == 10

    # Duty cycle.
    assert app.duty_edit.text() == "10"
    assert app.duty == 10

    # Step size.
    assert app.step_size_edit.text() == "0.0001"
    assert app.step_size == 0.0001

    # Accuracy.
    assert app.accuracy_edit.text() == "4"
    assert app.value_accuracy == 4

    # Pulse on time / Pulse Width.
    assert app.pulse_on_time == 0.01


def test_button(app, qtbot):
    """
    Test Buttons.
    """
    # Set new freq. f= 100 Hz
    app.freq_edit.setText("100")
    qtbot.mouseClick(app.button, QtCore.Qt.MouseButton.LeftButton)

    assert app.freq_edit.text() == "100"
    assert app.freq == 100
    assert app.time_period == 0.01   # 1/100
    assert app.pulse_on_time == 0.001
    assert app.step_size == 1e-5
    assert app.value_accuracy == 5

    # Cycle Knob.
    qtbot.mouseClick(app.dial_freq, QtCore.Qt.MouseButton.LeftButton)
    assert app.dial_freq.value() == 36
    assert app.number_of_cycles == 36

    # Time Delay Knob.
    qtbot.mouseClick(app.dial, QtCore.Qt.MouseButton.LeftButton)
    assert app.dial.value() == 350
    assert app.intervel == 350


def test_monitor(app, qtbot):
    """
    Monitor Output.
    """
    app.freq_edit.setText("10")
    app.voltage_edit.setText("10.0")

    monitor_output = f"""\
        Voltage:        {app.voltage} VDC
        Frequency:      {app.freq} Hz
        Time Period:    {app.time_period} Sec
        Duty Cycle:     {app.duty} %
        Pulse width:    {app.pulse_on_time} Sec
        Step Size:      {app.step_size}
        No. Cycles:     {app.number_of_cycles}
        Accuracy Value: {app.value_accuracy} Decimals"""

    qtbot.mouseClick(app.button, QtCore.Qt.MouseButton.LeftButton)
    assert app.monitor_textbox.toPlainText() == monitor_output


def load_values(test_app):
    """
    Class variables.
    """
    test_app.freq = 10
    test_app.value_accuracy = 2 + len(f"{test_app.freq}") if test_app.freq % 2 == 0 else 1 + len(f"{test_app.freq}")
    test_app.time_period = round(1/test_app.freq, test_app.value_accuracy)
    test_app.voltage = 10.0
    test_app.duty = 10
    test_app.step_size = 1/10 ** (len(f"{test_app.freq}") + 2)
    test_app.intervel = 10
    test_app.pulse_on_time = round(1 / test_app.freq * (test_app.duty / 100), test_app.value_accuracy)
    test_app.suggested_step, test_app.suggested_accuracy = test_app.step_size, test_app.value_accuracy
    test_app.number_of_cycles = 4
    test_app.start_x_axis = 0.0
    test_app.end_x_axis = round((1/test_app.freq) * test_app.number_of_cycles, test_app.value_accuracy)
    test_app.pulse_end, test_app.pulse_start = test_app.pulse_on_time, 0.0
