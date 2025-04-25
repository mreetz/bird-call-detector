# db.py
import mysql.connector
from db_config import MYSQL_CONFIG

class Database:
    def __init__(self):
        self.conn = mysql.connector.connect(**MYSQL_CONFIG)
        self.cursor = self.conn.cursor()

    def insert_detection(self, species, timestamp, confidence):
        query = """
            INSERT INTO detections (species, timestamp, confidence)
            VALUES (%s, %s, %s)
        """
        self.cursor.execute(query, (species, timestamp, confidence))
        self.conn.commit()

    def close(self):
        self.cursor.close()
        self.conn.close()

    def insert_daily_summary(self, timestamp):
        query = """
            INSERT INTO daily_summary (summary_date, species, count)
            SELECT DATE(timestamp), species, COUNT(*)
            FROM detections
            WHERE DATE(timestamp) = %s
            GROUP BY species
        """
        self.cursor.execute(query, (timestamp))
        self.conn.commit()