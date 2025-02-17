# advanced_intraday_strategy.py
import threading
import time
import pandas as pd
from datetime import datetime
from helper_angel import login_trading, getHistorical, getNiftyExpiryDate, placeOrder
from angel_subscribe_n1 import ltpDict  # Realtime prices

# ========== STRATEGY CONFIGURATION ==========
CONFIG = {
    'symbol': 'NIFTY',            # Trading instrument
    'expiry': getNiftyExpiryDate(),# Auto-fetch expiry
    'lot_size': 75,               # Contract quantity
    'risk_percent': 1.5,          # Risk per trade (% of capital)
    'rr_ratio': 1.5,              # Risk:Reward ratio
    'max_trades': 3,              # Maximum simultaneous trades
    'timeframe': '5min',          # 5min/15min/30min
    'paper_trading': 1,           # 1=Paper, 0=Live
    'trading_hours': {            # Strategy active hours
        'start': datetime.strptime('09:30', '%H:%M').time(),
        'end': datetime.strptime('14:30', '%H:%M').time()
    }
}

class AdvancedIntradayStrategy:
    def __init__(self):
        self.active_trades = []
        self.trade_history = []
        self.capital = 100000      # Starting capital
        self.total_pnl = 0         # Cumulative P&L
        login_trading()            # Connect to Angel One
        
    def is_market_open(self):
        """Check if within trading hours"""
        now = datetime.now().time()
        return CONFIG['trading_hours']['start'] <= now <= CONFIG['trading_hours']['end']

    def calculate_signals(self):
        """Generate signals using EMA crossover and RSI"""
        while True:
            try:
                if not self.is_market_open():
                    time.sleep(60)
                    continue

                symbol = f"NSE:{CONFIG['symbol']}"
                hist_data = getHistorical(symbol, CONFIG['timeframe'], 2)
                
                # Calculate indicators
                hist_data['ema_9'] = hist_data['close'].ewm(span=9, adjust=False).mean()
                hist_data['ema_21'] = hist_data['close'].ewm(span=21, adjust=False).mean()
                hist_data['rsi'] = self.calculate_rsi(hist_data['close'], 14)
                
                # Current market data
                current_price = ltpDict.get(symbol)
                ema_9 = hist_data['ema_9'].iloc[-1]
                ema_21 = hist_data['ema_21'].iloc[-1]
                rsi = hist_data['rsi'].iloc[-1]
                
                # Generate signals
                if ema_9 > ema_21 and rsi > 50 and current_price > ema_9:
                    self.execute_trade('BUY', current_price)
                elif ema_9 < ema_21 and rsi < 50 and current_price < ema_9:
                    self.execute_trade('SELL', current_price)
                    
                time.sleep(300)  # Check every 5 minutes
                
            except Exception as e:
                print(f"Error: {str(e)}")
                time.sleep(60)

    def execute_trade(self, direction, entry_price):
        """Execute option trade with dynamic parameters"""
        if len(self.active_trades) >= CONFIG['max_trades']:
            return

        # Calculate strike price
        strike_offset = 100 if CONFIG['symbol'] == 'NIFTY' else 200
        strike = (round(entry_price/strike_offset) * strike_offset) + (
            strike_offset if direction == 'BUY' else -strike_offset)

        # Create option symbol
        option_type = 'CE' if direction == 'BUY' else 'PE'
        symbol = f"NFO:{CONFIG['symbol']}{CONFIG['expiry']}{strike}{option_type}"

        # Risk management calculations
        position_size = int((CONFIG['risk_percent']/100 * self.capital) / (
            entry_price * CONFIG['lot_size']))
        stop_loss = entry_price * 0.98 if direction == 'BUY' else entry_price * 1.02
        take_profit = entry_price * (1 + CONFIG['rr_ratio']/100) if direction == 'BUY' else entry_price * (1 - CONFIG['rr_ratio']/100)

        # Place order
        order_id = placeOrder(
            symbol=symbol,
            t_type='BUY',
            qty=CONFIG['lot_size'] * position_size,
            order_type='MARKET',
            price=0,
            variety='NORMAL',
            papertrading=CONFIG['paper_trading']
        )
        
        if order_id:
            trade = {
                'order_id': order_id,
                'symbol': symbol,
                'direction': direction,
                'entry': entry_price,
                'sl': stop_loss,
                'tp': take_profit,
                'quantity': CONFIG['lot_size'] * position_size,
                'status': 'OPEN',
                'entry_time': datetime.now()
            }
            self.active_trades.append(trade)
            print(f"{direction} {symbol} @ {entry_price}")

    def manage_trades(self):
        """Auto-manage open positions with trailing SL"""
        while True:
            for trade in self.active_trades.copy():
                current_price = ltpDict.get(trade['symbol'])
                
                if current_price:
                    # Update trailing SL
                    if trade['direction'] == 'BUY':
                        new_sl = max(trade['sl'], current_price * 0.995)
                    else:
                        new_sl = min(trade['sl'], current_price * 1.005)
                    
                    # Check exit conditions
                    if (current_price <= new_sl and trade['direction'] == 'BUY') or \
                       (current_price >= new_sl and trade['direction'] == 'SELL'):
                        self.exit_trade(trade, current_price, 'SL')
                    elif (current_price >= trade['tp'] and trade['direction'] == 'BUY') or \
                         (current_price <= trade['tp'] and trade['direction'] == 'SELL'):
                        self.exit_trade(trade, current_price, 'TP')
            
            time.sleep(5)

    def exit_trade(self, trade, exit_price, reason):
        """Close trade and update capital"""
        placeOrder(
            symbol=trade['symbol'],
            t_type='SELL',
            qty=trade['quantity'],
            order_type='MARKET',
            price=0,
            variety='NORMAL',
            papertrading=CONFIG['paper_trading']
        )
        pnl = (exit_price - trade['entry']) * trade['quantity'] if trade['direction'] == 'BUY' \
              else (trade['entry'] - exit_price) * trade['quantity']
        self.capital += pnl
        self.total_pnl += pnl
        trade.update({
            'exit': exit_price,
            'pnl': pnl,
            'exit_time': datetime.now(),
            'status': 'CLOSED',
            'exit_reason': reason
        })
        self.trade_history.append(trade)
        self.active_trades.remove(trade)
        print(f"Closed {trade['symbol']} @ {exit_price} ({reason}) P&L: {pnl:.2f}")

    def calculate_rsi(self, prices, period=14):
        """Calculate RSI indicator"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(period).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs))

    def generate_report(self):
        """Generate end-of-day performance report"""
        if self.trade_history:
            report = pd.DataFrame(self.trade_history)
            report.to_csv(f"trade_report_{datetime.now().date()}.csv", index=False)
            print(f"📊 Trade Report Saved: {len(report)} Trades | Total P&L: {self.total_pnl:.2f}")

# ========== MAIN EXECUTION ==========
if __name__ == "__main__":
    strategy = AdvancedIntradayStrategy()
    
    strategy_thread = threading.Thread(target=strategy.calculate_signals)
    manage_thread = threading.Thread(target=strategy.manage_trades)
    
    strategy_thread.start()
    manage_thread.start()
    
    print("🚀 Advanced Intraday Strategy Active 🎯")
    print("Monitoring EMA + RSI Signals...")
    
    # Generate report at end of day
    while True:
        if not strategy.is_market_open() and strategy.trade_history:
            strategy.generate_report()
            break
        time.sleep(60)
