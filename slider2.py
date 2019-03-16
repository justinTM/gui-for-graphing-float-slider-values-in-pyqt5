#!/usr/bin/env python3

# print('importing packages...')

# 'sys' used for cmd arguments
# import sys  

# PyQt5 is the gui package used in this program
from PyQt5.QtWidgets import QApplication, QSlider, QPushButton, QDialog, QLabel, QHBoxLayout, QWidget, QVBoxLayout, QMainWindow
from PyQt5.QtCore import Qt, pyqtSignal

# this matplotlib backend, qt5agg, allows us to draw a graph inside
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt

# from random import random  

# math.sqrt() math.isclose()
import math

# custom class from file 'msd.py'
# file should be in same directory as execution of this program
from msd import MassSpringDamper


class DoubleSlider(QSlider):
    """
    Overrides the default QSlider, which only handles int values
    Adds float functionality in a limited form (only value get and set)
    
    Use 'DoubleSlider().valueChanged.connect()' to connect a callback function
    to the movement of a Qslider.
    """
    def __init__(self, min_val=0, max_val=1, num_ticks=10):
        super().__init__(Qt.Horizontal)
        # super().setMinimum(min_val)
        
        super().setMinimum(0)
        super().setMaximum(num_ticks)
        
        self._min_value = min_val
        self._max_value = max_val
        self._max_int = num_ticks
        
        self.setValue((abs(self._max_value)-abs(self._min_value))/2)
        
    def _value_range(self):
        return self._max_value - self._min_value

    def value(self):
        """
        returns a float value representation of the
        integer super class
        """
        scale_factor = (1 / self._max_int) * self._value_range()
        int_value = super().value()
        scaled_value = round(float(int_value) * scale_factor, 3)
        corrected_value = scaled_value + self._min_value
        # print('scale factor: {}\nint_value: {}\nscaled_value: {}\ncorrected_value: {}'.format(
        #     scale_factor, int_value, scaled_value, corrected_value))
        return corrected_value

    def setValue(self, value):
        super().setValue(int((value - self._min_value) / self._value_range() * self._max_int))        


class SliderWidget(QWidget):
    """
    Places an updating-text QLabel to the left of a slider
    into a sub widget
    """
    def __init__(self, label, min_val, max_val, num_ticks):
        super().__init__()
        
        # Create Slider and Label
        self.mySlider = DoubleSlider(min_val,
                                     max_val,
                                     num_ticks, )
        self.label = QLabel(label)
        self.label_text = label
        self.set_slider_label(min_val)
        
        # Align label to left of mySlider
        self.layout = QHBoxLayout()
        self.setLayout(self.layout)
        
        # Adding the widgets
        self.layout.addWidget(self.label)
        self.layout.addWidget(self.mySlider)
        
        self.mySlider.valueChanged.connect(self.set_slider_label)
    
    def value(self):
        return self.mySlider.value()
    
    def set_slider_label(self, value):
        self.label.setText('{0}: {1:.3f}'.format(
            self.label_text, self.mySlider.value()))


class SidebarWidget(QWidget):
    def __init__(self, layout=None):
        print('Instantiating SidebarWidget()')
        self.layout = QVBoxLayout()
        self.category_label_text = 'Type: '
        self.category_label = QLabel(self.category_label_text)
        self.sliders = [
            ('mass', SliderWidget('Mass', 0, 10, 1000)),
            ('spring', SliderWidget('Spring', 0, 10, 1000)),
            ('damper', SliderWidget('Damper', 0, 10, 1000)),
            ('time', SliderWidget('Time (s)', 0, 100, 1000)),
            ('time_step', SliderWidget('Time Step (s)', 0.001, 0.1, 100)), 
            ('initial_x', SliderWidget('Initial x', -10, 10, 200)), 
            ('initial_x_dot', SliderWidget('Initial dx', -1, 1, 200)),
        ]
        
        self.add_titled_widget(QLabel('System Parameters'), 
                               [slider for name, slider in self.sliders if name in ['mass', 'spring', 'damper']])
       
        self.add_titled_widget(QLabel('System Behavior'), [
                               self.category_label])
        
        self.add_titled_widget(QLabel('Simulation Parameters'),
                               [slider for name, slider in self.sliders if name in ['time', 'time_step', 'initial_x', 'initial_x_dot']])
    
    def add_titled_widget(self, title_qlabel, list_of_qwidgets, layout=None):
        """
        adds a layout to SidebarWidget with the following widgets:
            a title for this widget, title_qlabel,
            each QWidget in list_of_qwidgets

        title_qlabel: QLabel title of this widget
        list_of_qwidgets: list of QWidget objects

        (optional) layout:
            give QVBoxLayout() or QHBoxLayout().
            default is QVBoxLayout()
        """
        if layout: this_layout = layout
        else:
            this_layout = QVBoxLayout()
                    
        this_layout.addWidget(title_qlabel)
        for qwidget in list_of_qwidgets:    
            this_layout.addWidget(qwidget)
            
        self.layout.addLayout(this_layout)
    
    def get_slider_values(self):
        """
        returns a list of tuples:
            (slider_name, slider_value)
        for example:
            [('spring', 1.219), ('mass', 0.713)]
        """
        slider_vals = {}
        for slider_name, slider in self.sliders:
            slider_vals[slider_name] = slider.value()
        return slider_vals


class Grapher(QMainWindow):
    def __init__(self):
        """
        The main code written for this assignment begins here in Grapher.__init__()
        """
        self.slider_values = []
        QMainWindow.__init__(self)
        self.setWindowTitle('Mass Spring Damper')

        # Control buttons for the interface
        quit_button = QPushButton('Quit')
        quit_button.clicked.connect(app.exit)

        simulate_button = QPushButton('Simulate System')
        simulate_button.clicked.connect(self._simulate_button_pressed)

        # The display for the graph
        self.figure = Figure()
        self.display = FigureCanvas(self.figure)
        self.figure.clear()

        # The layout of the interface
        widget = QWidget()
        self.setCentralWidget(widget)    
        
        # adding sidebar    
        self.sidebar = SidebarWidget()
        self.sidebar.layout.addStretch()
        self.sidebar.layout.addWidget(simulate_button)
        self.sidebar.layout.addWidget(quit_button)
        
        # connect slots to slider value change signals
        for slider_name, slider in self.sidebar.sliders:
            # print('adding signal to {}'.format(slider_name))
            slider.mySlider.valueChanged.connect(self._slider_values_updated)
        
        # create a layout to place the graph and sidebar next to each other
        top_level_layout = QHBoxLayout()
        widget.setLayout(top_level_layout)
        
        # add the FigureCanvas as a wdiget to the layout
        top_level_layout.addLayout(self.sidebar.layout)
        top_level_layout.addWidget(self.display)
        
        # update slider labels and print them out
        self._slider_values_updated()
    
    def _slider_values_updated(self):
        """
        called whenever a QSlider is adjusted by the user
        
        - gets a dictionary of slider values by name in SidebarWidget
        - updates the text label next to the slider
        
        """
        self.slider_values = self.sidebar.get_slider_values()
        m = self.slider_values['mass']
        k = self.slider_values['spring']
        c = self.slider_values['damper']
        
        self._update_category_label(m, k, c)
        print(self.slider_values)
    
    def _update_category_label(self, m, k, c):
        """
        evaluate the category of the mass spring damper system
        based on slider values (mass is m, k is spring, c is damper).
        """
        critical_damping_coeff = 2 * math.sqrt(k * m)
        if critical_damping_coeff:
            damping_ratio = c / critical_damping_coeff
        else:
            damping_ratio = 0

        category = ''
        if damping_ratio >= 0 and damping_ratio < 1:
            category = 'Underdamped'
        if math.isclose(damping_ratio, 0, rel_tol=1e-01):
            category = 'Undamped'
        elif damping_ratio > 1:
            category = 'Overdamped'
        elif math.isclose(damping_ratio, 1, rel_tol=1e-01):
            category = 'Critically damped'

        # msd = MassSpringDamper(svs['mass'], svs['spring'], svs['damper'])

        label_text = self.sidebar.category_label_text
        self.sidebar.category_label.setText('{0}{1}'.format(
            label_text, category))
    
    def _simulate_button_pressed(self):
        """
        Called when a user presses the button.
        
        Runs the MassSpringDamper() code fed with the slider values for simulator parameters then calls graph()
        """
        # slider values from sidebar
        self.slider_values = self.sidebar.get_slider_values()
        svs = self.slider_values
        if svs['mass'] == 0:
            svs['mass'] = 0.01
            
        # create a simulator from class found in 'msd.py'
        msd = MassSpringDamper(svs['mass'], svs['spring'], svs['damper'])
        
        # rename some variables for clarity with msd.simulate() arg names
        x0 = svs['initial_x']
        x_dot0 = svs['initial_x_dot']
        t = svs['time']
        t_step = svs['time_step']
        
        # invoke the simulator()
        states, times = msd.simulate(x0, x_dot0, t, t_step)
        # print(states, times)
        
        self.graph(states, times)
    
    def graph(self, states, times):
        # states = [x, x_dot]
        try:
            initial_position = states[0][0]
        except:
            initial_position = 0
        # extract 2nd element (displacement) from list of [x, x_dot]'s
        displacements = [state[0] - initial_position for state in states]
        self.draw(times, displacements)

    def draw(self, times, displacements):
        self.figure.clear()
        
        # subplot usage: subplot([nrows][ncols][index (top left to right)])
        ax = self.figure.add_subplot(111)
        ax.plot(times, displacements)
        
        # set title and axis labels
        ax.set(xlabel='time (s)', ylabel='displacement of Mass-Spring-Damper (distance)',
               title='Displacement of Mass-Spring-Damper system over time\n\
                   k = {}, m = {}, c = {}, dt = {:.3f}'.format(
                   self.slider_values['spring'],
                   self.slider_values['mass'],
                   self.slider_values['damper'],
                   self.slider_values['initial_x_dot'], 
                   ))
        # scale x-axis from slider value (y-axis usually auto-scaled)
        ax.set_xlim([0, self.slider_values['time']])
        ax.grid()
        # call FigureCanvas framework qt5agg
        self.display.draw()


if __name__ == '__main__':
    """
    __main__ is the entry point for this program, meaning the first line of code executed after setting up (importing packages, etc.).

    QApplication() comes from the package PyQt5
    Grapher() is our "main" custom classs utilizing PyQt5 code

    Attention should be paid to Grapher.__init__() which houses the main GUI code (generating the sidebar using sub classes, getting values from sliders, creating the graph, etc.). Additionally, DoubleSlider() which has been modified from code shared by user jdreaver as 'double_slider.py' on github as of March 2019.
    
    Slider values are printed out to the console to illustrate the behind-the-scenes.
    """
    app = QApplication([])

    gui = Grapher()

    gui.show()

    app.exec_()
