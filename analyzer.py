# analyzer.py - Crypto Analysis Engine
import aiohttp
import asyncio
from datetime import datetime
import logging
from typing import Dict, List
import statistics

from config import (
    BINANCE_ENDPOINTS, TIMEFRAMES, MIN_CONFIDENCE,
    VOLUME_SPIKE_THRESHOLD, MIN_VOLUME_RATIO,
    STRUCTURE_CONFIDENCE_THRESHOLD, TREND_STRENGTH_THRESHOLD,
    TP_LEVELS, SL_PERCENT, MIN_RR_RATIO
)

logger = logging.getLogger(__name__)

class CryptoAnalyzer:
    def __init__(self):
        self.session = None
    
    async def get_session(self):
        """Get or create aiohttp session"""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()
        return self.session
    
    async def close_session(self):
        """Close aiohttp session"""
        if self.session and not self.session.closed:
            await self.session.close()
    
    async def get_current_price(self, symbol: str) -> float:
        """Get current price for a symbol"""
        try:
            session = await self.get_session()
            url = f"{BINANCE_ENDPOINTS['price']}?symbol={symbol}"
            
            async with session.get(url) as response:
                data = await response.json()
                return float(data['price'])
        
        except Exception as e:
            logger.error(f"Error getting price for {symbol}: {e}")
            return 0.0
    
    async def get_klines(self, symbol: str, interval: str, limit: int = 100) -> List[Dict]:
        """Get kline/candlestick data"""
        try:
            session = await self.get_session()
            url = f"{BINANCE_ENDPOINTS['klines']}?symbol={symbol}&interval={interval}&limit={limit}"
            
            async with session.get(url) as response:
                data = await response.json()
                
                candles = []
                for candle in data:
                    candles.append({
                        'time': candle[0],
                        'open': float(candle[1]),
                        'high': float(candle[2]),
                        'low': float(candle[3]),
                        'close': float(candle[4]),
                        'volume': float(candle[5])
                    })
                
                return candles
        
        except Exception as e:
            logger.error(f"Error getting klines for {symbol} {interval}: {e}")
            return []
    
    async def get_24h_ticker(self, symbol: str) -> Dict:
        """Get 24h ticker data"""
        try:
            session = await self.get_session()
            url = f"{BINANCE_ENDPOINTS['ticker']}?symbol={symbol}"
            
            async with session.get(url) as response:
                data = await response.json()
                return {
                    'volume': float(data['volume']),
                    'quote_volume': float(data['quoteVolume']),
                    'price_change_percent': float(data['priceChangePercent']),
                    'high': float(data['highPrice']),
                    'low': float(data['lowPrice'])
                }
        
        except Exception as e:
            logger.error(f"Error getting ticker for {symbol}: {e}")
            return {}
    
    def analyze_trend(self, candles: List[Dict]) -> Dict:
        """Analyze trend from candles"""
        if len(candles) < 20:
            return {'direction': 'NEUTRAL', 'strength': 0}
        
        closes = [c['close'] for c in candles]
        
        # Calculate moving averages
        ma20 = statistics.mean(closes[-20:])
        ma50 = statistics.mean(closes[-50:]) if len(closes) >= 50 else ma20
        
        current_price = closes[-1]
        
        # Determine trend
        if current_price > ma20 and ma20 > ma50:
            direction = 'LONG'
            strength = ((current_price - ma50) / ma50) * 100
        elif current_price < ma20 and ma20 < ma50:
            direction = 'SHORT'
            strength = ((ma50 - current_price) / ma50) * 100
        else:
            direction = 'NEUTRAL'
            strength = 0
        
        # Calculate trend consistency
        higher_highs = sum(1 for i in range(1, min(10, len(candles))) 
                          if candles[-i]['high'] > candles[-i-1]['high'])
        higher_lows = sum(1 for i in range(1, min(10, len(candles))) 
                         if candles[-i]['low'] > candles[-i-1]['low'])
        
        consistency = (higher_highs + higher_lows) / 20 * 100 if direction == 'LONG' else 0
        
        if direction == 'SHORT':
            lower_highs = 10 - higher_highs
            lower_lows = 10 - higher_lows
            consistency = (lower_highs + lower_lows) / 20 * 100
        
        return {
            'direction': direction,
            'strength': abs(strength),
            'consistency': consistency,
            'ma20': ma20,
            'ma50': ma50
        }
    
    def analyze_volume(self, candles: List[Dict]) -> Dict:
        """Analyze volume patterns"""
        if len(candles) < 20:
            return {'score': 0, 'spike': False}
        
        volumes = [c['volume'] for c in candles]
        avg_volume = statistics.mean(volumes[:-5])
        recent_volume = statistics.mean(volumes[-5:])
        
        volume_ratio = recent_volume / avg_volume if avg_volume > 0 else 0
        
        # Check for volume spike
        spike = volume_ratio > VOLUME_SPIKE_THRESHOLD
        
        # Calculate volume score
        if volume_ratio >= VOLUME_SPIKE_THRESHOLD:
            score = 100
        elif volume_ratio >= MIN_VOLUME_RATIO:
            score = (volume_ratio / VOLUME_SPIKE_THRESHOLD) * 100
        else:
            score = 50
        
        return {
            'score': min(100, score),
            'ratio': volume_ratio,
            'spike': spike,
            'avg_volume': avg_volume,
            'recent_volume': recent_volume
        }
    
    def find_support_resistance(self, candles: List[Dict]) -> Dict:
        """Find support and resistance levels"""
        if len(candles) < 50:
            return {'support': 0, 'resistance': 0}
        
        highs = [c['high'] for c in candles[-50:]]
        lows = [c['low'] for c in candles[-50:]]
        
        # Simple method: recent high/low
        resistance = max(highs)
        support = min(lows)
        
        current_price = candles[-1]['close']
        
        # Find nearest levels
        upper_levels = sorted([h for h in highs if h > current_price])
        lower_levels = sorted([l for l in lows if l < current_price], reverse=True)
        
        nearest_resistance = upper_levels[0] if upper_levels else resistance
        nearest_support = lower_levels[0] if lower_levels else support
        
        return {
            'resistance': nearest_resistance,
            'support': nearest_support,
            'range': nearest_resistance - nearest_support
        }
    
    def calculate_entry_exit(self, current_price: float, direction: str, 
                            support: float, resistance: float) -> Dict:
        """Calculate entry, stop loss, and take profit levels"""
        
        if direction == 'LONG':
            entry = current_price * 0.999  # Slightly below current price
            stop_loss = entry * (1 - SL_PERCENT)
            
            # Calculate take profits
            tp1 = entry * (1 + TP_LEVELS['TP1'])
            tp2 = entry * (1 + TP_LEVELS['TP2'])
            tp3 = entry * (1 + TP_LEVELS['TP3'])
            tp4 = entry * (1 + TP_LEVELS['TP4'])
        
        else:  # SHORT
            entry = current_price * 1.001  # Slightly above current price
            stop_loss = entry * (1 + SL_PERCENT)
            
            # Calculate take profits
            tp1 = entry * (1 - TP_LEVELS['TP1'])
            tp2 = entry * (1 - TP_LEVELS['TP2'])
            tp3 = entry * (1 - TP_LEVELS['TP3'])
            tp4 = entry * (1 - TP_LEVELS['TP4'])
        
        # Calculate Risk/Reward ratio
        risk = abs(entry - stop_loss)
        reward = abs(tp4 - entry)
        rr_ratio = reward / risk if risk > 0 else 0
        
        return {
            'entry': round(entry, 6),
            'stop_loss': round(stop_loss, 6),
            'take_profits': [
                round(tp1, 6),
                round(tp2, 6),
                round(tp3, 6),
                round(tp4, 6)
            ],
            'rr_ratio': round(rr_ratio, 2)
        }
    
    async def analyze_coin(self, symbol: str) -> Dict:
        """Complete analysis of a coin"""
        try:
            logger.info(f"Analyzing {symbol}...")
            
            # Get data for multiple timeframes
            timeframe_analyses = {}
            all_candles = {}
            
            for tf, params in TIMEFRAMES.items():
                candles = await self.get_klines(symbol, tf, params['limit'])
                if candles:
                    all_candles[tf] = candles
                    
                    trend = self.analyze_trend(candles)
                    volume = self.analyze_volume(candles)
                    levels = self.find_support_resistance(candles)
                    
                    timeframe_analyses[tf] = {
                        'trend': trend,
                        'volume': volume,
                        'levels': levels,
                        'weight': params['weight']
                    }
            
            if not timeframe_analyses:
                logger.warning(f"No data available for {symbol}")
                return {'confidence': 0}
            
            # Combine analyses from all timeframes
            combined_score = 0
            total_weight = 0
            directions = []
            
            for tf, analysis in timeframe_analyses.items():
                trend = analysis['trend']
                volume = analysis['volume']
                weight = analysis['weight']
                
                # Calculate score for this timeframe
                tf_score = 0
                
                # Trend score (40%)
                if trend['strength'] >= TREND_STRENGTH_THRESHOLD:
                    tf_score += 40
                
                # Consistency score (30%)
                if trend['consistency'] >= 70:
                    tf_score += 30
                
                # Volume score (30%)
                if volume['score'] >= 80:
                    tf_score += 30
                
                combined_score += tf_score * weight
                total_weight += weight
                
                if trend['direction'] != 'NEUTRAL':
                    directions.append(trend['direction'])
            
            # Average score
            final_score = (combined_score / total_weight) if total_weight > 0 else 0
            
            # Determine final direction
            if not directions:
                return {'confidence': 0}
            
            long_count = directions.count('LONG')
            short_count = directions.count('SHORT')
            
            if long_count > short_count:
                final_direction = 'LONG'
                alignment_bonus = (long_count / len(directions)) * 100
            elif short_count > long_count:
                final_direction = 'SHORT'
                alignment_bonus = (short_count / len(directions)) * 100
            else:
                return {'confidence': 0}
            
            # Adjust final score with alignment
            final_score = (final_score + alignment_bonus) / 2
            
            # Round to integer
            confidence = int(round(final_score))
            
            # If confidence is not 100%, return early
            if confidence < MIN_CONFIDENCE:
                logger.info(f"{symbol}: Confidence {confidence}% - Below threshold")
                return {'confidence': confidence}
            
            # Get current price and levels
            current_price = await self.get_current_price(symbol)
            main_tf_levels = timeframe_analyses['1h']['levels']
            
            # Calculate entry and exit points
            trade_levels = self.calculate_entry_exit(
                current_price,
                final_direction,
                main_tf_levels['support'],
                main_tf_levels['resistance']
            )
            
            # Check RR ratio
            if trade_levels['rr_ratio'] < MIN_RR_RATIO:
                logger.info(f"{symbol}: RR ratio {trade_levels['rr_ratio']} - Below minimum")
                return {'confidence': 0}
            
            logger.info(f"{symbol}: ✅ Signal found! Confidence: {confidence}%, Direction: {final_direction}")
            
            return {
                'symbol': symbol,
                'confidence': confidence,
                'direction': final_direction,
                'entry': trade_levels['entry'],
                'stop_loss': trade_levels['stop_loss'],
                'take_profits': trade_levels['take_profits'],
                'rr_ratio': trade_levels['rr_ratio'],
                'current_price': current_price,
                'analysis_time': datetime.now().isoformat()
            }
        
        except Exception as e:
            logger.error(f"Error analyzing {symbol}: {e}")
            return {'confidence': 0}
