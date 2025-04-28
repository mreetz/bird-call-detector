# db.py
import mysql.connector
from db_config import MYSQL_CONFIG

class Database:
    def __init__(self):
        self.conn = mysql.connector.connect(**MYSQL_CONFIG)
        self.cursor = self.conn.cursor()

    def insert_detection(self, species, timestamp, confidence):
        """Insert a new detection record into the database."""
        query = """
            INSERT INTO detections (species, timestamp, confidence)
            VALUES (%s, %s, %s)
        """
        self.cursor.execute(query, (species, timestamp, confidence))
        self.conn.commit()

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

    def fetch_recent_detections(self, limit=10):
        """Fetch the most recent detections."""
        query = """
            SELECT species, timestamp, confidence
            FROM detections
            ORDER BY timestamp DESC
            LIMIT %s
        """
        self.cursor.execute(query, (limit,))
        results = self.cursor.fetchall()
        return results

    def delete_old_detections(self, days_old=30):
        """Delete detections older than a certain number of days."""
        query = """
            DELETE FROM detections
            WHERE timestamp < NOW() - INTERVAL %s DAY
        """
        self.cursor.execute(query, (days_old,))
        self.conn.commit()

    def close(self):
        """Close the database connection cleanly."""
        self.cursor.close()
        self.conn.close()





    

    

  
    