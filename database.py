# database.py - Database Management
import sqlite3
from datetime import datetime, timedelta
from typing import List, Dict
import logging

from config import DATABASE_FILE, ADMIN_ID

logger = logging.getLogger(__name__)

class Database:
    def __init__(self):
        self.db_file = DATABASE_FILE
        self.init_database()
    
    def get_connection(self):
        """Get database connection"""
        return sqlite3.connect(self.db_file)
    
    def init_database(self):
        """Initialize database tables"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                joined_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_blocked BOOLEAN DEFAULT 0,
                is_active BOOLEAN DEFAULT 1
            )
        ''')
        
        # Admins table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS admins (
                admin_id INTEGER PRIMARY KEY,
                added_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Signals table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS signals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                signal_number INTEGER,
                coin TEXT,
                direction TEXT,
                entry REAL,
                stop_loss REAL,
                tp1 REAL,
                tp2 REAL,
                tp3 REAL,
                tp4 REAL,
                rr_ratio REAL,
                sent_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'active',
                profit_percent REAL DEFAULT 0,
                closed_time TIMESTAMP
            )
        ''')
        
        # Analyzed coins table (for cooldown tracking)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS analyzed_coins (
                coin TEXT PRIMARY KEY,
                last_analysis TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Add main admin if not exists
        cursor.execute('INSERT OR IGNORE INTO admins (admin_id) VALUES (?)', (ADMIN_ID,))
        
        conn.commit()
        conn.close()
        
        logger.info("Database initialized successfully")
    
    # User management
    def add_user(self, user_id: int, username: str, first_name: str):
        """Add or update user"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO users (user_id, username, first_name)
            VALUES (?, ?, ?)
        ''', (user_id, username, first_name))
        
        conn.commit()
        conn.close()
    
    def block_user(self, user_id: int):
        """Block a user"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('UPDATE users SET is_blocked = 1 WHERE user_id = ?', (user_id,))
        
        conn.commit()
        conn.close()
        
        logger.info(f"User {user_id} blocked")
    
    def unblock_user(self, user_id: int):
        """Unblock a user"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('UPDATE users SET is_blocked = 0 WHERE user_id = ?', (user_id,))
        
        conn.commit()
        conn.close()
        
        logger.info(f"User {user_id} unblocked")
    
    def is_user_blocked(self, user_id: int) -> bool:
        """Check if user is blocked"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT is_blocked FROM users WHERE user_id = ?', (user_id,))
        result = cursor.fetchone()
        
        conn.close()
        
        return result and result[0] == 1
    
    def get_all_active_users(self) -> List[int]:
        """Get all active (not blocked) users"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT user_id FROM users WHERE is_blocked = 0 AND is_active = 1')
        users = [row[0] for row in cursor.fetchall()]
        
        conn.close()
        
        return users
    
    # Admin management
    def is_admin(self, user_id: int) -> bool:
        """Check if user is admin"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT admin_id FROM admins WHERE admin_id = ?', (user_id,))
        result = cursor.fetchone()
        
        conn.close()
        
        return result is not None
    
    def add_admin(self, admin_id: int):
        """Add new admin"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('INSERT OR IGNORE INTO admins (admin_id) VALUES (?)', (admin_id,))
        
        conn.commit()
        conn.close()
        
        logger.info(f"Admin {admin_id} added")
    
    def remove_admin(self, admin_id: int):
        """Remove admin (except main admin)"""
        if admin_id == ADMIN_ID:
            logger.warning("Cannot remove main admin")
            return False
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM admins WHERE admin_id = ?', (admin_id,))
        
        conn.commit()
        conn.close()
        
        logger.info(f"Admin {admin_id} removed")
        return True
    
    def get_all_admins(self) -> List[int]:
        """Get all admins"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT admin_id FROM admins')
        admins = [row[0] for row in cursor.fetchall()]
        
        conn.close()
        
        return admins
    
    # Signal management
    def add_signal(self, coin: str, direction: str, entry: float, 
                   stop_loss: float, take_profits: List[float], rr_ratio: float) -> int:
        """Add new trading signal"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Get today's signal count
        signal_number = self.get_today_signal_count() + 1
        
        cursor.execute('''
            INSERT INTO signals 
            (signal_number, coin, direction, entry, stop_loss, tp1, tp2, tp3, tp4, rr_ratio)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (signal_number, coin, direction, entry, stop_loss, 
              take_profits[0], take_profits[1], take_profits[2], take_profits[3], rr_ratio))
        
        signal_id = cursor.lastrowid
        
        conn.commit()
        conn.close()
        
        logger.info(f"Signal #{signal_number} added for {coin}")
        return signal_id
    
    def update_signal_status(self, signal_id: int, status: str, profit_percent: float):
        """Update signal status"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE signals 
            SET status = ?, profit_percent = ?, closed_time = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (status, profit_percent, signal_id))
        
        conn.commit()
        conn.close()
        
        logger.info(f"Signal {signal_id} updated: {status}, profit: {profit_percent}%")
    
    def get_active_signals(self) -> List[Dict]:
        """Get all active signals"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, signal_number, coin, direction, entry, stop_loss, 
                   tp1, tp2, tp3, tp4, rr_ratio, sent_time
            FROM signals
            WHERE status = 'active'
        ''')
        
        signals = []
        for row in cursor.fetchall():
            signals.append({
                'id': row[0],
                'signal_number': row[1],
                'coin': row[2],
                'direction': row[3],
                'entry': row[4],
                'stop_loss': row[5],
                'take_profits': [row[6], row[7], row[8], row[9]],
                'rr_ratio': row[10],
                'sent_time': row[11]
            })
        
        conn.close()
        
        return signals
    
    def get_today_signal_count(self) -> int:
        """Get count of signals sent today"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        today = datetime.now().date()
        cursor.execute('''
            SELECT COUNT(*) FROM signals 
            WHERE DATE(sent_time) = ?
        ''', (today,))
        
        count = cursor.fetchone()[0]
        
        conn.close()
        
        return count
    
    def get_daily_stats(self) -> Dict:
        """Get daily trading statistics"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        today = datetime.now().date()
        
        # Total signals
        cursor.execute('''
            SELECT COUNT(*) FROM signals 
            WHERE DATE(sent_time) = ?
        ''', (today,))
        total_signals = cursor.fetchone()[0]
        
        # Wins
        cursor.execute('''
            SELECT COUNT(*) FROM signals 
            WHERE DATE(sent_time) = ? AND status = 'completed' AND profit_percent > 0
        ''', (today,))
        wins = cursor.fetchone()[0]
        
        # Losses
        cursor.execute('''
            SELECT COUNT(*) FROM signals 
            WHERE DATE(sent_time) = ? AND status = 'stopped'
        ''', (today,))
        losses = cursor.fetchone()[0]
        
        # Active signals
        cursor.execute('''
            SELECT COUNT(*) FROM signals 
            WHERE DATE(sent_time) = ? AND status = 'active'
        ''', (today,))
        active = cursor.fetchone()[0]
        
        # Total profit
        cursor.execute('''
            SELECT SUM(profit_percent) FROM signals 
            WHERE DATE(sent_time) = ? AND status IN ('completed', 'stopped')
        ''', (today,))
        total_profit = cursor.fetchone()[0] or 0
        
        # Average profit
        completed = wins + losses
        avg_profit = total_profit / completed if completed > 0 else 0
        
        # Win rate
        win_rate = (wins / completed * 100) if completed > 0 else 0
        
        conn.close()
        
        return {
            'total_signals': total_signals,
            'wins': wins,
            'losses': losses,
            'active_signals': active,
            'total_profit': round(total_profit, 2),
            'avg_profit': round(avg_profit, 2),
            'win_rate': round(win_rate, 1)
        }
    
    # Analyzed coins management
    def mark_coin_analyzed(self, coin: str):
        """Mark coin as analyzed"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO analyzed_coins (coin, last_analysis)
            VALUES (?, CURRENT_TIMESTAMP)
        ''', (coin,))
        
        conn.commit()
        conn.close()
    
    def was_recently_analyzed(self, coin: str, cooldown_minutes: int = 120) -> bool:
        """Check if coin was analyzed recently"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cutoff = datetime.now() - timedelta(minutes=cooldown_minutes)
        
        cursor.execute('''
            SELECT last_analysis FROM analyzed_coins 
            WHERE coin = ? AND last_analysis > ?
        ''', (coin, cutoff))
        
        result = cursor.fetchone()
        
        conn.close()
        
        return result is not None
