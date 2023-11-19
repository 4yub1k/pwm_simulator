import logging

from pyqtgraph import mkPen, PlotWidget
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QGridLayout,
    QLabel,
    QDial,
    QCheckBox,
    QLineEdit,
    QPushButton,
    QComboBox,
    QPlainTextEdit
)
from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtGui import QPalette, QColor, QIcon
from numpy import arange, sin, pi          # , cos, linspace


class MainWindow(QMainWindow):
    """
    PWM Simulator, This app can simulate the Pulse acccording to user provided values.
    You can fine tune the output. By Changing Accuracy and Step size.
    It will Log every to simulator.log file, To log everything select DEBUG level.
    Author: Salah Ud Din.
    GitHub: https://github.com/4yub1k
    YouTube: https://www.youtube.com/@nerdyayubi
    """
    freq = 10                                       # Hz
    value_accuracy = 2 + len(f"{freq}") if freq % 2 == 0 else 1 + len(f"{freq}")  # increase accuracy for odd freq.
    time_period = round(1/freq, value_accuracy)     # Time period
    voltage = 5.0                                   # Volts
    duty = 10                                       # 10 %
    step_size = 1/10 ** (len(f"{freq}") + 2)        # Step by which graph increment values. (timeperiod/freq)
    intervel = 10                                   # mSecs, QTimer
    pulse_on_time = round(1 / freq * (duty / 100), value_accuracy)
    graph_chk_off = False                           # Off/ON graph of duty
    graph_chk_sine = False                          # show sine wave.
    suggested_step, suggested_accuracy = step_size, value_accuracy

    """For X- Axis Configuration"""
    number_of_cycles = 4                          # Numbers of cycles to show at a time on plot. Also for Knob
    start_x_axis = 0.0
    end_x_axis = round((1/freq) * number_of_cycles, value_accuracy)  # End of x-axis, t=1/f = 1/1000 = 0.001 * 10 = 0.01, remove 1 zero to adjust the scale.
    pulse_end, pulse_start = pulse_on_time, 0.0
    global_index_counter = 0.0

    def __init__(self, logger):
        """
        Main window of APP, Gridlayout is used.
        Where initial plots are plotted. Button, and Check boxex are added. QTimer Is defined
        """
        super().__init__()

        self.logger = logger
        self.logger.info(
            f"""Initialized with values....
            Frequency: {self.freq}
            Time Period: {self.time_period}
            Voltage: {self.voltage}
            Duty Cycle: {self.duty}
            Step Size: {self.step_size}
            Intervel: {self.intervel}
            Pulse width: {self.pulse_on_time}
            No. Cycles: {self.number_of_cycles}
            Start x-axis: {self.start_x_axis}
            End x-axis: {self.end_x_axis}
            Round Value point: {self.value_accuracy}
            """
        )
        self.setWindowTitle("PWM Simulator/Generator")
        self.grid_layout = QGridLayout()

        self.plt = PlotWidget()
        self.setCentralWidget(self.plt)
        self.plt.setYRange(0, self.voltage + 2)
        self.plt.showGrid(x=True, y=True)
        self.setWindowIcon(QIcon("icon.ico"))
        self.plt.setTitle("PWM Simulator/Generator", color="w", size="20pt", font="bold")

        styles = {"color": "red", "font-size": "14px"}
        self.plt.setLabel("left", "Voltage (V)", **styles)
        self.plt.setLabel("bottom", "Frequency (Hz)(1-sec)", **styles)

        self.plt.addLegend(brush=(0, 0, 255, 50), labelTextColor="w", offset=1, colCount=3)
        self.legend = self.plt.plotItem.legend

        # Generate X - Axis.
        # f = 10 Hz, T = 1/10 = 0.1, range 0 -> 0.1, and wih steps, 0.1/10 = 0.01 (step_size = timeperiod/freq)
        self.x_axis = list(round(n, self.value_accuracy) for n in arange(0.0, self.time_period * self.number_of_cycles, self.step_size))
        self.plt.setXRange(0.0, self.end_x_axis)
        self.logger.debug(
            f"""
            x-Axis generated; Size: {len(self.x_axis)},
            Plot Start: {0.0} Plot End: {self.time_period * self.number_of_cycles}
            """
        )

        # PWM ON state Graph.
        self.y_axis_on = self.y_axis()
        pen = mkPen(color=(0, 255, 0))
        self.line_graph = self.plt.plot(self.x_axis, self.y_axis_on, pen=pen, fillLevel=0.0, brush=(0, 255, 0, 100))
        self.logger.debug(f"Y- Axis size for ON state: {len(self.y_axis_on)}")

        # Update Legend values dynamically.
        self.update_legend()

        # PWM OFF state Graph.
        self.y_axis_off = [0] * len(self.x_axis)
        self.line_graph_off = self.plt.plot(self.x_axis, self.y_axis_off, fillLevel=0.0, brush=(255, 0, 0, 100))  # (r,g,b,a), a = fill level
        self.logger.debug(f"Y- Axis size for OFF state: {len(self.y_axis_on)}")

        # Plot Sine Wave. (Frequeny is already included in X Axis)
        self.sine_y = [0] * len(self.x_axis)
        self.sine_wave = self.plt.plot(self.x_axis, self.sine_y, pen=mkPen(color=(255, 0, 0)))
        self.logger.debug(f"Y- Axis size for SINE: {len(self.y_axis_on)}")

        self.grid_layout.addWidget(self.plt, 0, 0, 1, 0)  # last 0, 1 will expand, rowSpan, columSpan

        # Time Delay Label
        self.label_interval = QLabel(f"Time (Delay): {self.intervel}ms")
        self.grid_layout.addWidget(self.label_interval, 1, 3, alignment=Qt.AlignmentFlag.AlignCenter)

        # Frequency Label
        self.label_frequency = QLabel(f"Cycles: {self.number_of_cycles}")
        self.grid_layout.addWidget(self.label_frequency, 1, 0, alignment=Qt.AlignmentFlag.AlignCenter)

        self.dailer_button()        # Add Knob to GUI
        self.dailer_freq_button()   # Frequency Knob.
        self.variable_input()       # Add Inputs, and Buttons to GUI.
        self.log_buttons()          # Enable to write logs to file.
        self.monitor()              # Shows timeperiod etc

        self.grid_layout.addWidget(QLabel("Salah Ud Din | GitHub: @4yub1k"), 1, 2, alignment=Qt.AlignmentFlag.AlignCenter)

        # Update Monitor:
        self.monitor_textbox.insertPlainText(self.monitor_update())

        # Add Grid inside vertical Box layout.
        widget = QWidget()
        widget.setLayout(self.grid_layout)
        self.setCentralWidget(widget)

        # Timer
        self.timer = QTimer()                   # time = QTimer(self), or call with instance.
        self.timer.setInterval(self.intervel)
        self.timer.timeout.connect(self.update_plot)
        self.timer.start()

    def update_plot(self):
        """
        Update axis by removing firt value of list, and then appending single value to their list (at end).
        Controlled by QTimer().
        """
        # Update X axis Range.
        self.start_x_axis += self.step_size
        self.end_x_axis += self.step_size
        self.plt.setXRange(self.start_x_axis, self.end_x_axis)
        self.logger.debug(f"Plot updating--plot Start: {self.start_x_axis}, Plot End: {self.end_x_axis}")

        # Update X axis values.
        self.x_axis = self.x_axis[1:]
        self.x_axis.append(self.x_axis[-1] + self.step_size)
        self.logger.debug(f"Plot updating--X Axis value appended: {self.x_axis[-1] + self.step_size}")

        # PWM ON state update graph------------------------.
        self.y_axis_on = self.y_axis_on[1:]
        self.y_axis_on.append(self.update_y_axis(self.global_index_counter, self.x_axis[-1]))
        self.line_graph.setData(self.x_axis, self.y_axis_on)
        self.global_index_counter += 1      # Keep updaeing global index counter.
        self.logger.debug(f"Plot updating--Y Axis ON value appended: {self.y_axis_on[-1]}")
        self.logger.debug(f"Plot updating--Global Counter: {self.global_index_counter}")

        # PWM OFF state Update graph-------------------------.
        self.y_axis_off = self.y_axis_off[1:]
        self.y_axis_off.append(0.0 if self.y_axis_on[-1] == self.voltage else self.voltage)

        # # Check if Show PWM OFF cycle button is checked or not.
        if self.graph_chk_off:
            self.line_graph_off.setData(self.x_axis, self.y_axis_off)
        else:
            self.y_axis_off = [0] * len(self.x_axis)
            self.line_graph_off.setData(self.x_axis, self.y_axis_off)

        # Sine Wave update graph---------------------------.
        self.sine_y = self.sine_y[1:]
        self.sine_y.append(self.voltage * sin(2 * pi * self.freq * self.x_axis[-1]))
        self.logger.debug(f"Plot updating--Y Axis SINE value appended: {self.sine_y[-1]}")

        # Check if show sine wave button is checked or not.
        if self.graph_chk_sine:
            self.sine_wave.setData(self.x_axis, self.sine_y)
        else:
            # Populate y axis with zeros, to turn off graph. shortcut :)
            self.sine_y = [0] * len(self.x_axis)
            self.sine_wave.setData(self.x_axis, self.sine_y)
            # asyncio.run(self.update_axis(self.x_axis, self.sine_y))

    def y_axis(self):
        """
        Generate Y axis, use return or use self.y_axis. //Temporary Solution.// Problem with rounding
        """
        y_axis_new = []
        self.pulse_start = 0.0
        self.pulse_end = round(self.pulse_on_time, self.value_accuracy)
        self.length = round(len(self.x_axis) / self.number_of_cycles)   # axis length/frequency
        for index, value in enumerate(self.x_axis, start=0):
            """
            Don't do operation in if statements, it will mess up accuracy/code,
            I believe it is due to number of digits after decimal point.
            """
            if index % self.length == 0.0 and value != 0.0:
                self.pulse_start = self.pulse_start + self.time_period
                self.pulse_end = self.pulse_end + self.time_period
            if self.pulse_start <= value and value <= self.pulse_end:
                y_axis_new.append(self.voltage)
            else:
                y_axis_new.append(0.0)
        self.global_index_counter = len(self.x_axis)
        return y_axis_new

    def update_y_axis(self, index, value):
        """
        Add single value to Y Axis.
        """
        if index % self.length == 0.0 and value != 0.0:
            self.pulse_start = self.pulse_start + self.time_period
            self.pulse_end = self.pulse_end + self.time_period
            self.logger.debug(f"Update--Start: {self.pulse_start}, Value: {value}, Pulse Width: {self.pulse_on_time}, Time period: {self.time_period}, End: {self.pulse_end}")
        if value >= self.pulse_start and value <= self.pulse_end:
            return self.voltage
        else:
            return 0.0

    def update_legend(self):
        """
        Call whenever you have update the freq, Voltage, Pusle value.
        """
        self.legend.clear()
        self.legend.addItem(self.line_graph, f"Frequency: {self.freq} Hz")
        self.legend.addItem(self.line_graph, f"Voltage: {self.voltage} VDC")
        self.legend.addItem(self.line_graph, f"Pulse ON: {self.pulse_on_time:0.{self.value_accuracy}f} Sec")
        self.logger.info(f"Legend Updated-- Frequnecy: {self.freq}, Voltage: {self.voltage}, Pulse ON: {self.pulse_on_time:0.9f}")

    def dailer_button(self):
        """
        Dailer button, Increase/Decrease the Time interval between updating the axis values using QTimer.
        It controls the QTimer. self.timer.setInterval(self.intervel)
        """
        self.dial = QDial()
        self.dial.setStyleSheet("background-color: #B8B8B8")
        self.dial.setFixedHeight(100)
        self.dial.setFixedWidth(100)
        self.dial.setMinimum(0)
        self.dial.setMaximum(1000)
        self.dial.setValue(10)
        self.dial.valueChanged.connect(self.dail_update_interval)
        self.grid_layout.addWidget(self.dial, 3, 3)

    def dailer_freq_button(self):
        """
        Dailer button, To control frequency, Number of cycles you want to show.
        """
        self.dial_freq = QDial()
        self.dial_freq.setObjectName("freq_dial")       # For sender().objectName().
        self.dial_freq.setStyleSheet("background-color: #B8B8B8")
        self.dial_freq.setFixedHeight(100)
        self.dial_freq.setFixedWidth(100)
        self.dial_freq.setMinimum(1)
        self.dial_freq.setMaximum(100)
        self.dial_freq.setValue(self.number_of_cycles)      # Default = 2.
        self.dial_freq.valueChanged.connect(self.dail_update_interval_freq)
        self.grid_layout.addWidget(self.dial_freq, 3, 0)

    def dail_update_interval(self):
        """
        Set new value (self.interval) of QTime when dailer is rotated.
        self.timer.setInterval(self.intervel)
        """
        self.intervel = self.dial.value()
        self.label_interval.setText(f"Time (Delay): {self.intervel}ms")
        self.timer.setInterval(self.intervel)
        self.logger.debug(f"Dial: Time Delay Rotated Value: {self.intervel}")

    def dail_update_interval_freq(self):
        """
        Adjust values of Frequency Knob.
        """
        intervel_freq = self.dial_freq.value()
        self.label_frequency.setText(f"Cycles: {intervel_freq}")
        self.number_of_cycles = intervel_freq
        self.button_update()
        self.logger.debug(f"Dial: Frequency Rotated Value: {intervel_freq}")

    def variable_input(self):
        """
        This method will create GUI for Inputs, Labels and Button shown near to the Knob.
        """
        form_layout = QGridLayout()

        # Input field: For Voltage input from GUI.
        self.voltage_edit = QLineEdit()
        self.voltage_edit.setStyleSheet("background-color: #B8B8B8")
        self.voltage_edit.setText(f"{self.voltage}")
        self.voltage_edit.setFixedWidth(50)
        self.voltage_label = QLabel("Voltage:")
        form_layout.addWidget(self.voltage_label, 0, 1)
        form_layout.addWidget(self.voltage_edit, 0, 2, alignment=Qt.AlignmentFlag.AlignLeft)

        # Input field: For Frequency.
        self.freq_edit = QLineEdit()
        self.freq_edit.setStyleSheet("background-color: #B8B8B8")
        self.freq_edit.setText(f"{self.freq}")
        self.freq_edit.setFixedWidth(50)
        freq_label = QLabel("Frequency:")
        form_layout.addWidget(freq_label, 1, 1)
        form_layout.addWidget(self.freq_edit, 1, 2, alignment=Qt.AlignmentFlag.AlignLeft)

        # Input field: For Duty Cycle.
        self.duty_edit = QLineEdit()
        self.duty_edit.setStyleSheet("background-color : #B8B8B8")
        self.duty_edit.setText(f"{self.duty}")
        self.duty_edit.setFixedWidth(50)
        duty_label = QLabel("Duty Cycle:")
        form_layout.addWidget(duty_label, 3, 1)
        form_layout.addWidget(self.duty_edit, 3, 2, alignment=Qt.AlignmentFlag.AlignLeft)

        # Input field: For Accuracy Value.
        self.accuracy_edit = QLineEdit()
        self.accuracy_edit.setStyleSheet("background-color : #B8B8B8")
        self.accuracy_edit.setText(f"{self.value_accuracy}")
        self.accuracy_edit.setFixedWidth(50)
        accuracy_label = QLabel("Accuracy:")
        form_layout.addWidget(accuracy_label, 4, 1)
        form_layout.addWidget(self.accuracy_edit, 4, 2, alignment=Qt.AlignmentFlag.AlignLeft)

        # Input field: For Step Size.
        self.step_size_edit = QLineEdit()
        self.step_size_edit.setStyleSheet("background-color : #B8B8B8")
        self.step_size_edit.setText(f"{self.step_size}")
        self.step_size_edit.setFixedWidth(50)
        step_size_label = QLabel("Step Size:")
        form_layout.addWidget(step_size_label, 5, 1)
        form_layout.addWidget(self.step_size_edit, 5, 2, alignment=Qt.AlignmentFlag.AlignLeft)

        # Push Button: For Re Plotting all Graphs based on the inputs from GUI.
        self.button = QPushButton("Update")
        self.button.setObjectName("Update")         # Used for sender().objectName()
        self.button.setStyleSheet("background-color: #B8B8B8")
        self.button.clicked.connect(self.button_update)
        form_layout.addWidget(self.button, 6, 1, 2, 2)

        # Push Button: Pause the Graph.
        self.pause_button = QPushButton("Pause")
        self.pause_button.setCheckable(True)    # set it as toggle button.
        self.pause_button.setStyleSheet("background-color: #B8B8B8")
        self.pause_button.clicked.connect(self.pause_button_update)
        form_layout.addWidget(self.pause_button, 6, 0, 2, 1)

        # Check Button:  For showing the OFF state area of Pulse, Red color graph.
        self.chk_button = QCheckBox("Show OFF Cycle")
        self.chk_button.stateChanged.connect(self.button_update)
        form_layout.addWidget(self.chk_button, 0, 0)

        # Check Button:  For Sine wave show/hide.
        self.chk_button_sine = QCheckBox("Show Sine Wave")
        self.chk_button_sine.stateChanged.connect(self.button_update)
        form_layout.addWidget(self.chk_button_sine, 1, 0)

        # Label: For warning message, which will be shown when Exception is raised.
        self.warning = QLabel()
        self.warning.setStyleSheet("color: red")
        form_layout.addWidget(self.warning, 3, 0)

        # Label: For Step Size suggestion MIN.
        self.step_size_label = QLabel(f"Step Size (min): {self.suggested_step}")
        self.step_size_label.setStyleSheet("background-color: #000000; color: #7CFC00")
        form_layout.addWidget(self.step_size_label, 5, 0)

        # Label: For Accuracy suggestion MIN.
        self.accuracy_label = QLabel(f"Accuracy (min): {self.suggested_accuracy}")
        self.accuracy_label.setStyleSheet("background-color: #000000; color: #7CFC00")
        form_layout.addWidget(self.accuracy_label, 4, 0)

        form_layout.setContentsMargins(10, 0, 10, 10)  # left, top, right, bottom from sides.
        self.grid_layout.addLayout(form_layout, 3, 2, alignment=Qt.AlignmentFlag.AlignRight)
        self.logger.debug("Input for GUI initialized...")

    def log_buttons(self):
        """
        Logging: Label and Dropdown.
        """
        log_grid = QGridLayout()

        log_label = QLabel("Logs Level: ")
        log_grid.addWidget(log_label, 0, 0)

        log_combo = QComboBox()
        log_combo.setStyleSheet("background-color: #000000; color: #7CFC00")
        log_combo.addItems(["INFO", "DEBUG"])
        log_combo.setFixedWidth(80)
        log_combo.activated.connect(self.option)
        log_grid.addWidget(log_combo, 0, 1)

        self.grid_layout.addLayout(log_grid, 1, 1, alignment=Qt.AlignmentFlag.AlignCenter)

    def option(self, option_num):
        """
        Drop  Down: Logs
        """
        match option_num:
            case 0:
                self.logger.setLevel(logging.INFO)
            case 1:
                self.logger.setLevel(logging.DEBUG)

    def monitor(self):
        """
        Monitor to show some usefull data for user.
        """
        monitor_grid = QGridLayout()

        monitor_label = QLabel("Monitor")
        monitor_grid.addWidget(monitor_label, 1, 1, alignment=Qt.AlignmentFlag.AlignCenter)

        self.monitor_textbox = QPlainTextEdit()
        self.monitor_textbox.setStyleSheet("background-color: #000000; color: #7CFC00")
        # self.monitor_textbox.setMaximumWidth(250)
        self.monitor_textbox.setReadOnly(True)
        monitor_grid.addWidget(self.monitor_textbox, 2, 1)
        self.grid_layout.addLayout(monitor_grid, 3, 1, alignment=Qt.AlignmentFlag.AlignCenter)

    def monitor_update(self):
        return f"""\
        Voltage:        {self.voltage} VDC
        Frequency:      {self.freq} Hz
        Time Period:    {self.time_period} Sec
        Duty Cycle:     {self.duty} %
        Pulse width:    {self.pulse_on_time} Sec
        Step Size:      {self.step_size}
        No. Cycles:     {self.number_of_cycles}
        Accuracy Value: {self.value_accuracy} Decimals"""

    def pause_button_update(self):
        """
        Toggle Button: To Pause/Resume the graph.
        """
        if self.pause_button.isChecked():
            self.pause_button.setText("Resume")
            self.timer.stop()
        else:
            self.pause_button.setText("Pause")
            self.timer.start()
        self.logger.debug(f"Pause Button Pressed, State: {self.pause_button.isChecked()},Text : {self.pause_button.text()}")

    def button_update(self,):
        """
        This is the Update Button, which will re plot the graphs for new values.
        """
        # Use can "Button groups" or sender() for large number of buttons in order to know which button is clicked.
        self.logger.debug("Update button pushed..")

        # Update exceptions.
        class LowFrequency(Exception):
            pass

        class FloatDuty(Exception):
            pass

        class StepNegative(Exception):
            pass

        try:
            self.graph_chk_off = self.chk_button.isChecked()
            self.graph_chk_sine = self.chk_button_sine.isChecked()

            # No need for voltage check.
            if len(self.freq_edit.text()) <= 1 or self.freq_edit.text().isalpha():
                raise LowFrequency
            if not self.duty_edit.text().isdecimal():
                raise FloatDuty
            if float(self.step_size_edit.text()) < 0 or float(self.step_size_edit.text()) == 1:
                raise StepNegative
            """
            I have used objectName, as you can set it for a button of any type,
            If you are dealing with just Button not dailers than you can use sender().text(),
            sender().text() can be used with any button which has setText() method.
            """
            if self.sender().objectName() in ["Update", "freq_dial"]:
                self.logger.debug(f"Button used: {self.sender().objectName()}")
                # print(self.sender())
                # print(self.sender().objectName())
                self.voltage = float(self.voltage_edit.text() if len(self.voltage_edit.text()) else self.voltage)
                self.freq = int(self.freq_edit.text() if len(self.freq_edit.text()) else self.freq)
                self.suggested_accuracy = 2 + len(f"{self.freq}") if self.freq % 2 == 0 else 1 + len(f"{self.freq}")  # Increase accuracy for odd freq.
                self.value_accuracy = self.suggested_accuracy if int(self.accuracy_edit.text()) < self.suggested_accuracy else int(self.accuracy_edit.text())
                self.time_period = round(1/self.freq, self.value_accuracy)
                self.duty = int(self.duty_edit.text() if len(self.duty_edit.text()) else self.duty)
                self.suggested_step = 1/10 ** (len(f"{self.freq}") + 2)
                self.step_size = self.suggested_step if float(self.step_size_edit.text()) > self.suggested_step else float(self.step_size_edit.text()) 
                self.step_size_edit.setText(f"{self.step_size}")
                self.accuracy_edit.setText(f"{self.value_accuracy}")

                self.global_index_counter = 0.0
                self.start_x_axis, self.end_x_axis = 0.0, (1/self.freq) * self.number_of_cycles
                self.plt.setXRange(self.start_x_axis, self.end_x_axis)

                self.pulse_on_time = round(1 / self.freq * (self.duty / 100), self.value_accuracy)
                self.update_legend()
                self.logger.info(
                    f"""Initialized with values....
                    Frequency: {self.freq}
                    Time Period: {self.time_period}
                    Voltage: {self.voltage}
                    Duty Cycle: {self.duty}
                    Step Size: {self.step_size}
                    Intervel: {self.intervel}
                    Pulse width: {self.pulse_on_time}
                    No. Cycles: {self.number_of_cycles}
                    Start x-axis: {self.start_x_axis}
                    End x-axis: {self.end_x_axis}
                    Round Value point: {self.value_accuracy}
                    Global Counter: {self.global_index_counter}
                    """
                )
                # Generate X - Axis.
                self.x_axis = list(round(n, self.value_accuracy) for n in arange(0.0, self.time_period * self.number_of_cycles, self.step_size))
                self.y_axis_on = self.y_axis()
                self.logger.debug(
                    f"""
                    x-Axis generated; Size: {len(self.x_axis)},
                    Plot Start: {0.0} Plot End: {self.time_period * self.number_of_cycles}
                    """
                )

            if self.chk_button.isChecked():
                self.logger.debug("Show Off cycle: Checked")
                self.y_axis_off = list(map(lambda v: 0.0 if v == self.voltage else self.voltage, self.y_axis_on))
            if self.chk_button_sine.isChecked():
                self.logger.debug("Show Sine Wave: Checked")
                self.sine_y = [self.voltage * sin(2 * pi * self.freq * value) for value in self.x_axis]

            # Update Monitor
            self.monitor_textbox.clear()
            self.monitor_textbox.insertPlainText(self.monitor_update())

        except LowFrequency:
            self.warning.setText("Freq must be above 1")
        except FloatDuty:
            self.warning.setText("Duty cycle range 1 - 100")
        except StepNegative:
            self.warning.setText("Step Size, 0 > value < 1")
        except ValueError:
            self.warning.setText("Only Float/Integer allowed")
        else:
            self.warning.clear()

        self.step_size_label.setText(f"Step Size (min): \n{self.step_size}")   # Update label of step size.suggested_step
        self.accuracy_label.setText(f"Accuracy (min): \n{self.suggested_accuracy}")   # Update label of step size.suggested_step
        self.plt.setYRange(0, self.voltage + 2)

        if self.graph_chk_sine:
            self.plt.setYRange(-(self.voltage + 2), self.voltage + 2)


if __name__ == "__main__":
    app = QApplication([])

    # You can also changle color by using self.setStyleSheet() inside __init__().
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor(53, 53, 53))
    palette.setColor(QPalette.ColorRole.WindowText, QColor(255, 255, 255))
    palette.setColor(QPalette.ColorRole.Base, QColor(25, 25, 25))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor(25, 25, 25))
    palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(255, 255, 255))
    palette.setColor(QPalette.ColorRole.Button, QColor(53, 53, 53))     # Sub Menus
    palette.setColor(QPalette.ColorRole.Highlight, QColor(255, 255, 255))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor(0, 0, 0))
    app.setPalette(palette)

    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)

    handle = logging.FileHandler(filename="simulator.log")
    format = logging.Formatter("[%(levelname)s]: %(asctime)s: %(funcName)s: %(message)s")
    handle.setFormatter(format)
    logger.addHandler(handle)

    main = MainWindow(logger)
    main.show()
    app.exec()
