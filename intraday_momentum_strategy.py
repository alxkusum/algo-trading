# intraday_momentum_strategy.py
import threading
import time
import pandas as pd
from helper_angel import login_trading, getHistorical, getNiftyExpiryDate, placeOrder
from angel_subscribe_n1 import ltpDict  # Realtime prices

# ========== STRATEGY CONFIGURATION ==========
CONFIG = {
    'symbol': 'NIFTY',            # Trading instrument
    'expiry': getNiftyExpiryDate(),# Auto-fetch expiry
    'lot_size': 50,               # Contract quantity
    'risk_percent': 1.5,          # Risk per trade (% of capital)
    'rr_ratio': 1.5,              # Risk:Reward ratio
    'max_trades': 3,              # Maximum simultaneous trades
    'timeframe': '5min',          # 5min/15min/30min
    'paper_trading': 1            # 1=Paper, 0=Live
}

class IntradayMomentum:
    def __init__(self):
        self.active_trades = []
        self.capital = 100000      # Starting capital
        login_trading()            # Connect to Angel One
        
    def calculate_vwap_signal(self):
        """Generate signals using VWAP and Volume Spike"""
        while True:
            try:
                symbol = f"NSE:{CONFIG['symbol']}"
                hist_data = getHistorical(symbol, CONFIG['timeframe'], 1)
                
                # Calculate VWAP
                hist_data['vwap'] = (hist_data['volume'] * 
                                   (hist_data['high'] + hist_data['low'] + hist_data['close'])/3).cumsum() / hist_data['volume'].cumsum()
                
                # Current market data
                current_price = ltpDict.get(symbol)
                current_vwap = hist_data['vwap'].iloc[-1]
                current_volume = hist_data['volume'].iloc[-1]
                avg_volume = hist_data['volume'].mean()
                
                # Generate signals
                if current_price > current_vwap and current_volume > avg_volume*1.5:
                    self.execute_trade('BUY', current_price)
                elif current_price < current_vwap and current_volume > avg_volume*1.5:
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
            self.active_trades.append({
                'order_id': order_id,
                'symbol': symbol,
                'direction': direction,
                'entry': entry_price,
                'sl': stop_loss,
                'tp': take_profit,
                'quantity': CONFIG['lot_size'] * position_size
            })
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
        self.active_trades.remove(trade)
        print(f"Closed {trade['symbol']} @ {exit_price} ({reason}) P&L: {pnl:.2f}")

# ========== MAIN EXECUTION ==========
if __name__ == "__main__":
    strategy = IntradayMomentum()
    
    strategy_thread = threading.Thread(target=strategy.calculate_vwap_signal)
    manage_thread = threading.Thread(target=strategy.manage_trades)
    
    strategy_thread.start()
    manage_thread.start()
    
    print("🎯 Intraday Momentum Strategy Active 🚀")
    print("Monitoring VWAP + Volume Breakouts...")