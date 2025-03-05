import sqlite3
from datetime import datetime

class Database:
    def __init__(self, db_name='air_quality.db'):
        self.conn = sqlite3.connect(db_name, check_same_thread=False)
        self.create_table()

    def create_table(self):
        cursor = self.conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS readings (
                timestamp TEXT PRIMARY KEY,
                pm25 REAL,
                pm10 REAL
            )
        ''')
        self.conn.commit()

    def insert_reading(self, pm25, pm10):
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                INSERT INTO readings (timestamp, pm25, pm10)
                VALUES (?, ?, ?)
            ''', (datetime.now().isoformat(), pm25, pm10))
            self.conn.commit()
        except sqlite3.IntegrityError:
            pass

    def get_history(self, limit=288):
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT * FROM readings 
            ORDER BY timestamp DESC 
            LIMIT ?
        ''', (limit,))
        return cursor.fetchall()

    def close(self):
        self.conn.close()
