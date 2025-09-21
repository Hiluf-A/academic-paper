import sqlite3
from datetime import datetime
import os

class DatabaseManager:
    def __init__(self, db_path="speed_monitor.db"):
        self.db_path = db_path
        self.init_database()

    def init_database(self):
        """Initialize database with required tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Create drivers table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS drivers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            license_plate TEXT UNIQUE NOT NULL,
            email TEXT NOT NULL,
            violation_count INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')

        # Create violations table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS violations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            driver_id INTEGER,
            speed REAL NOT NULL,
            timestamp TIMESTAMP NOT NULL,
            image_path TEXT NOT NULL,
            FOREIGN KEY (driver_id) REFERENCES drivers (id)
        )
        ''')

        conn.commit()
        conn.close()

    def add_driver(self, name, license_plate, email):
        """Add a new driver to the database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute('''
            INSERT INTO drivers (name, license_plate, email)
            VALUES (?, ?, ?)
            ''', (name, license_plate, email))
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
        finally:
            conn.close()

    def get_driver_info(self, license_plate):
        """Get driver information by license plate"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
        SELECT id, name, email, violation_count
        FROM drivers
        WHERE license_plate = ?
        ''', (license_plate,))

        result = cursor.fetchone()
        conn.close()

        if result:
            return {
                "id": result[0],
                "name": result[1],
                "email": result[2],
                "violation_count": result[3]
            }
        return None

    def add_violation(self, violation_data):
        """Add a new violation record"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            # Get driver ID
            cursor.execute('''
            SELECT id FROM drivers WHERE license_plate = ?
            ''', (violation_data["license_plate"],))
            
            driver_id = cursor.fetchone()
            
            if driver_id:
                # Add violation record
                cursor.execute('''
                INSERT INTO violations (driver_id, speed, timestamp, image_path)
                VALUES (?, ?, ?, ?)
                ''', (driver_id[0], violation_data["speed"], 
                      violation_data["timestamp"], violation_data["image_path"]))
                
                # Update violation count
                cursor.execute('''
                UPDATE drivers
                SET violation_count = violation_count + 1
                WHERE id = ?
                ''', (driver_id[0],))
                
                conn.commit()
                return True
            return False
        finally:
            conn.close()

    def get_violations(self, limit=10):
        """Get recent violations"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
        SELECT v.id, v.timestamp, v.speed, d.name, d.license_plate, v.image_path
        FROM violations v
        JOIN drivers d ON v.driver_id = d.id
        ORDER BY v.timestamp DESC
        LIMIT ?
        ''', (limit,))

        violations = cursor.fetchall()
        conn.close()

        return [{
            "id": v[0],
            "timestamp": v[1],
            "speed": v[2],
            "driver_name": v[3],
            "license_plate": v[4],
            "image_path": v[5]
        } for v in violations]

    def get_top_speeders(self, limit=5):
        """Get top speeders based on violation count"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
        SELECT name, license_plate, violation_count
        FROM drivers
        ORDER BY violation_count DESC
        LIMIT ?
        ''', (limit,))

        speeders = cursor.fetchall()
        conn.close()

        return [{
            "name": s[0],
            "license_plate": s[1],
            "violation_count": s[2]
        } for s in speeders]

    def get_all_drivers(self):
        """Get all drivers"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
        SELECT name, license_plate, email, violation_count, created_at
        FROM drivers
        ORDER BY created_at DESC
        ''')
        drivers = cursor.fetchall()
        conn.close()
        return [{
            "name": d[0],
            "license_plate": d[1],
            "email": d[2],
            "violation_count": d[3],
            "created_at": d[4]
        } for d in drivers]

    def update_driver(self, license_plate, name=None, email=None):
        """Update driver information"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        updates = []
        params = []
        if name:
            updates.append("name = ?")
            params.append(name)
        if email:
            updates.append("email = ?")
            params.append(email)
        if not updates:
            conn.close()
            return False
        params.append(license_plate)
        query = f"UPDATE drivers SET {', '.join(updates)} WHERE license_plate = ?"
        cursor.execute(query, params)
        conn.commit()
        updated = cursor.rowcount > 0
        conn.close()
        return updated

    def delete_driver(self, license_plate):
        """Delete a driver by license plate"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''DELETE FROM drivers WHERE license_plate = ?''', (license_plate,))
        conn.commit()
        deleted = cursor.rowcount > 0
        conn.close()
        return deleted

    def delete_violation(self, violation_id):
        """Delete a violation by id"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''DELETE FROM violations WHERE id = ?''', (violation_id,))
        conn.commit()
        deleted = cursor.rowcount > 0
        conn.close()
        return deleted 