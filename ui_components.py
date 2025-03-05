from kivy.uix.widget import Widget
from kivy.graphics import Color, Ellipse, Line
from kivy.properties import NumericProperty
import numpy as np

class Gauge(Widget):
    value = NumericProperty(0)
    min_val = 0
    max_val = 500

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.bind(value=self.redraw)
        self.bind(pos=self.redraw)
        self.bind(size=self.redraw)
        self.redraw()

    def get_color(self):
        if self.value < 50:
            return (0, 1, 0, 1)  # Green
        elif 50 <= self.value < 100:
            return (1, 1, 0, 1)  # Yellow
        else:
            return (1, 0, 0, 1)  # Red

    def redraw(self, *args):
        self.canvas.clear()
        with self.canvas:
            # Background
            Color(0.1, 0.1, 0.1, 1)
            Ellipse(pos=(self.center_x - 150, self.center_y - 150), size=(300, 300))
            
            # Gradient arc
            for i in range(180):
                angle = np.radians(i - 90)
                x = self.center_x + 140 * np.cos(angle)
                y = self.center_y + 140 * np.sin(angle)
                
                if i < 60:
                    Color(0, 1 - i/60, 0, 1)
                elif i < 120:
                    Color(i/60 - 1, 1, 0, 1)
                else:
                    Color(1, (180 - i)/60, 0, 1)
                    
                Line(points=[x, y, self.center_x, self.center_y], width=2)
            
            # Value indicator
            Color(*self.get_color())
            angle = np.radians((self.value / self.max_val) * 180 - 90)
            Line(
                points=[
                    self.center_x, self.center_y,
                    self.center_x + 140 * np.cos(angle),
                    self.center_y + 140 * np.sin(angle)
                ],
                width=4
            )
            
            # Value label
            Color(1, 1, 1, 1)
            self.canvas.add(
                Label(
                    text=f"{self.value:.1f} μg/m³",
                    font_size=30,
                    pos=(self.center_x - 50, self.center_y - 200)
                ).canvas
            )
