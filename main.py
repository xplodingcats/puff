import sys
import sqlite3
import serial
import threading
import time
import numpy as np
import matplotlib
matplotlib.use('Qt5Agg')
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure
import requests
import speech_recognition as sr
import pyttsx3

# Database handler
class Database:
    def __init__(self):
        self.conn = sqlite3.connect('air_quality.db', check_same_thread=False)
        self.create_table()

    def create_table(self):
        self.conn.execute('''
            CREATE TABLE IF NOT EXISTS readings (
                timestamp REAL PRIMARY KEY,
                pm25 REAL,
                pm10 REAL
            )
        ''')

    def insert_reading(self, pm25, pm10):
        self.conn.execute('''
            INSERT INTO readings (timestamp, pm25, pm10)
            VALUES (?, ?, ?)
        ''', (time.time(), pm25, pm10))
        self.conn.commit()

    def get_history(self, hours=24):
        cutoff = time.time() - (hours * 3600)
        cur = self.conn.cursor()
        cur.execute('SELECT * FROM readings WHERE timestamp > ?', (cutoff,))
        return cur.fetchall()

# Sensor reader thread
class SensorWorker(QThread):
    data_ready = pyqtSignal(float, float)

    def run(self):
        ser = serial.Serial('/dev/ttyUSB0', 9600, timeout=2)
        while True:
            data = ser.read(10)
            if len(data) == 10 and data[0] == 0xAA and data[1] == 0xC0:
                pm25 = (data[2] + data[3]*256)/10.0
                pm10 = (data[4] + data[5]*256)/10.0
                self.data_ready.emit(pm25, pm10)
            time.sleep(1)

# Speech Recognition Thread
class SpeechThread(QThread):
    audio_processed = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()

    def run(self):
        with self.microphone as source:
            self.recognizer.adjust_for_ambient_noise(source)
            audio = self.recognizer.listen(source)
            try:
                text = self.recognizer.recognize_sphinx(audio)
                self.audio_processed.emit(text)
            except Exception as e:
                self.audio_processed.emit(f"Error: {str(e)}")

# Text-to-Speech Handler
class TTSHandler:
    def __init__(self):
        self.engine = pyttsx3.init()
        self.engine.setProperty('rate', 150)
        self.engine.setProperty('volume', 1.0)

    def speak(self, text):
        self.engine.say(text)
        self.engine.runAndWait()

# Gauge widget
class Gauge(QWidget):
    def __init__(self):
        super().__init__()
        self.value = 0
        self.setMinimumSize(400, 400)
        self.setStyleSheet("background: transparent;")

    def setValue(self, value):
        self.value = value
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Draw background gradient
        gradient = QConicalGradient(self.width()/2, self.height()/2, -90)
        gradient.setColorAt(0.0, QColor('#4CAF50'))  # Green
        gradient.setColorAt(0.5, QColor('#FFEB3B'))  # Yellow
        gradient.setColorAt(1.0, QColor('#F44336'))   # Red
        painter.setBrush(gradient)
        painter.drawPie(50, 50, 300, 300, 0, 180*16)
        
        # Draw pointer
        angle = (self.value/500)*180 - 90
        painter.setPen(QPen(Qt.white, 5))
        painter.drawLine(200, 200, 
                        200 + 150*np.cos(np.radians(angle)),
                        200 + 150*np.sin(np.radians(angle)))
        
        # Draw value text
        painter.setFont(QFont('Arial', 30))
        painter.setPen(Qt.white)
        painter.drawText(50, 380, 300, 100, Qt.AlignCenter, f"{self.value:.1f} μg/m³")

# AI Assistant Widget
class PuffAI(QWidget):
    def __init__(self):
        super().__init__()
        self.sprites = {
            'idle': QPixmap('assets/sprites/idle.png'),
            'talking': QPixmap('assets/sprites/talking.png'),
            'alert': QPixmap('assets/sprites/alert.png'),
            'listening': QPixmap('assets/sprites/listening.png')
        }
        self.current_sprite = QLabel()
        self.current_sprite.setPixmap(self.sprites['idle'])
        self.tts = TTSHandler()
        self.layout = QVBoxLayout()
        self.layout.addWidget(self.current_sprite)
        self.setLayout(self.layout)

    def speak_response(self, text):
        self.current_sprite.setPixmap(self.sprites['talking'])
        self.tts.speak(text)
        self.current_sprite.setPixmap(self.sprites['idle'])

# History Tab with Matplotlib
class HistoryTab(QWidget):
    def __init__(self, db):
        super().__init__()
        self.db = db
        self.figure = Figure()
        self.canvas = FigureCanvasQTAgg(self.figure)
        layout = QVBoxLayout()
        layout.addWidget(self.canvas)
        self.setLayout(layout)
        self.plot_data()

    def plot_data(self):
        data = self.db.get_history()
        timestamps = [d[0] for d in data]
        pm25 = [d[1] for d in data]
        pm10 = [d[2] for d in data]

        self.figure.clear()
        ax = self.figure.add_subplot(111)
        ax.plot(timestamps, pm25, label='PM2.5')
        ax.plot(timestamps, pm10, label='PM10')
        ax.legend()
        ax.set_title('Air Quality History')
        self.canvas.draw()

# Settings Dialog
class SettingsDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Settings")
        
        layout = QVBoxLayout()
        
        # Theme Selection
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Light", "Dark"])
        layout.addWidget(QLabel("Theme:"))
        layout.addWidget(self.theme_combo)
        
        # Save Button
        save_btn = QPushButton("Save Settings")
        save_btn.clicked.connect(self.accept)
        layout.addWidget(save_btn)
        
        self.setLayout(layout)

# Main Window
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Air Quality Monitor")
        self.setGeometry(100, 100, 800, 600)
        self.db = Database()
        self.puff_ai = PuffAI()
        self.initUI()
        self.start_sensor()
        self.show_onboarding()

    def initUI(self):
        # Create central widget
        self.central_widget = QStackedWidget()
        self.setCentralWidget(self.central_widget)
        
        # Main Tab
        self.main_tab = QWidget()
        main_layout = QVBoxLayout()
        
        # Voice Interaction Button
        self.voice_btn = QPushButton("🎤 Speak to Puff")
        self.voice_btn.clicked.connect(self.start_voice_interaction)
        self.voice_btn.setStyleSheet("font-size: 20px; padding: 20px;")
        main_layout.addWidget(self.voice_btn)
        
        main_layout.addWidget(self.puff_ai)
        self.gauge = Gauge()
        main_layout.addWidget(self.gauge)
        self.main_tab.setLayout(main_layout)
        
        # History Tab
        self.history_tab = HistoryTab(self.db)
        
        # Settings Tab
        self.settings_dialog = SettingsDialog()
        
        # Add tabs to stacked widget
        self.central_widget.addWidget(self.main_tab)
        self.central_widget.addWidget(self.history_tab)
        
        # Side Menu
        self.menu = QToolBar("Menu")
        self.menu.setIconSize(QSize(32, 32))
        self.addToolBar(Qt.LeftToolBarArea, self.menu)
        
        # Menu Actions
        self.menu.addAction(QIcon('assets/menu.png'), "Main", lambda: self.central_widget.setCurrentIndex(0))
        self.menu.addAction(QIcon('assets/history.png'), "History", lambda: self.central_widget.setCurrentIndex(1))
        self.menu.addAction(QIcon('assets/settings.png'), "Settings", self.show_settings)
        
        # Status Bar
        self.status = self.statusBar()
        self.status.showMessage("Ready")
        self.status.setStyleSheet("color: white; background: #2c2c2c;")

    def start_sensor(self):
        self.sensor_worker = SensorWorker()
        self.sensor_worker.data_ready.connect(self.update_gauge)
        self.sensor_worker.start()

    def update_gauge(self, pm25, pm10):
        self.gauge.setValue(pm25)
        self.db.insert_reading(pm25, pm10)
        self.status.showMessage(f"PM2.5: {pm25:.1f} | PM10: {pm10:.1f}")

    def show_settings(self):
        self.settings_dialog.exec_()

    def show_onboarding(self):
        # Create onboarding dialog
        onboard = QDialog(self)
        onboard.setWindowTitle("Welcome to Puff!")
        layout = QVBoxLayout()
        
        # Add onboarding steps here
        layout.addWidget(QLabel("1. Connect your SDS011 sensor"))
        layout.addWidget(QLabel("2. Press the microphone to speak"))
        layout.addWidget(QLabel("3. View real-time data on the Main tab"))
        layout.addWidget(QLabel("4. Check historical data in History tab"))
        
        close_btn = QPushButton("Get Started")
        close_btn.clicked.connect(onboard.accept)
        layout.addWidget(close_btn)
        
        onboard.setLayout(layout)
        onboard.exec_()

    def start_voice_interaction(self):
        self.puff_ai.current_sprite.setPixmap(self.puff_ai.sprites['listening'])
        self.voice_thread = SpeechThread()
        self.voice_thread.audio_processed.connect(self.process_audio)
        self.voice_thread.start()

    def process_audio(self, text):
        self.puff_ai.current_sprite.setPixmap(self.puff_ai.sprites['talking'])
        response = f"You said: {text}"  # Replace with actual AI logic
        self.puff_ai.speak_response(response)
        self.puff_ai.current_sprite.setPixmap(self.puff_ai.sprites['idle'])

if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    
    # Setup dark theme
    dark_palette = QPalette()
    dark_palette.setColor(QPalette.Window, QColor(53, 53, 53))
    dark_palette.setColor(QPalette.WindowText, Qt.white)
    app.setPalette(dark_palette)
    
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
