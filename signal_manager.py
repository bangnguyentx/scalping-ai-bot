# signal_manager.py - Signal Management
import logging
from typing import Dict
from datetime import datetime

from config import ANALYSIS_COOLDOWN

logger = logging.getLogger(__name__)

class SignalManager:
    def __init__(self, db):
        self.db = db
    
    def was_recently_analyzed(self, coin: str) -> bool:
        """Check if coin was analyzed recently (within cooldown period)"""
        return self.db.was_recently_analyzed(coin, ANALYSIS_COOLDOWN)
    
    def mark_as_analyzed(self, coin: str):
        """Mark coin as analyzed"""
        self.db.mark_coin_analyzed(coin)
        logger.info(f"{coin} marked as analyzed - cooldown for {ANALYSIS_COOLDOWN} minutes")
    
    def check_take_profit(self, signal: Dict, current_price: float) -> bool:
        """Check if any take profit level is hit"""
        direction = signal['direction']
        take_profits = signal['take_profits']
        
        if direction == 'LONG':
            # For LONG, price should go UP to hit TP
            for tp in take_profits:
                if current_price >= tp:
                    logger.info(f"{signal['coin']}: TP hit at {current_price} (TP: {tp})")
                    return True
        
        else:  # SHORT
            # For SHORT, price should go DOWN to hit TP
            for tp in take_profits:
                if current_price <= tp:
                    logger.info(f"{signal['coin']}: TP hit at {current_price} (TP: {tp})")
                    return True
        
        return False
    
    def check_stop_loss(self, signal: Dict, current_price: float) -> bool:
        """Check if stop loss is hit"""
        direction = signal['direction']
        stop_loss = signal['stop_loss']
        
        if direction == 'LONG':
            # For LONG, SL is below entry
            if current_price <= stop_loss:
                logger.info(f"{signal['coin']}: SL hit at {current_price} (SL: {stop_loss})")
                return True
        
        else:  # SHORT
            # For SHORT, SL is above entry
            if current_price >= stop_loss:
                logger.info(f"{signal['coin']}: SL hit at {current_price} (SL: {stop_loss})")
                return True
        
        return False
    
    def calculate_profit(self, entry: float, exit_price: float, direction: str) -> float:
        """Calculate profit/loss percentage"""
        if direction == 'LONG':
            profit_percent = ((exit_price - entry) / entry) * 100
        else:  # SHORT
            profit_percent = ((entry - exit_price) / entry) * 100
        
        return round(profit_percent, 2)
    
    def get_highest_tp_hit(self, signal: Dict, current_price: float) -> int:
        """Get the highest TP level that was hit (1-4)"""
        direction = signal['direction']
        take_profits = signal['take_profits']
        
        highest_tp = 0
        
        for i, tp in enumerate(take_profits, 1):
            if direction == 'LONG':
                if current_price >= tp:
                    highest_tp = i
            else:  # SHORT
                if current_price <= tp:
                    highest_tp = i
        
        return highest_tp
    
    def calculate_rr_achieved(self, signal: Dict, current_price: float) -> float:
        """Calculate actual RR achieved"""
        entry = signal['entry']
        stop_loss = signal['stop_loss']
        
        risk = abs(entry - stop_loss)
        actual_reward = abs(current_price - entry)
        
        if risk > 0:
            rr_achieved = actual_reward / risk
            return round(rr_achieved, 2)
        
        return 0.0
