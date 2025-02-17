# angel_algo_strategy.py
import datetime
import threading
import time
import pandas as pd
from helper_angel import *

# Global configuration
STRATEGY_CONFIG = {
    'risk_per_trade': 0.02,        # 2% risk per trade
    'symbol': 'NIFTY',             # NIFTY|BANKNIFTY
    'lot_size': 50,
    'max_trades': 5,               # Max concurrent trades
    'paper_trading': 1,            # 1=Paper trade, 0=Real trade
    'order_type': 'MARKET',        # MARKET/LIMIT
    'strategy': 'BOLLINGER_RSI'    # BOLLINGER_RSI/MACD_CROSS
}

class AngelTradingStrategy:
    def __init__(self):
        self.active_trades = []
        self.historical_data = pd.DataFrame()
        self.initialize()

    def initialize(self):
        """Initialize connection and data feeds"""
        login_trading()
        print("Connected to Angel One Trading Account")
        
        # Start WebSocket feed from angel_subscribe_n1
        from angel_subscribe_n1 import ltpDict, token_list
        self.ltpDict = ltpDict
        self.token_list = token_list

    def bollinger_rsi_strategy(self):
        """Combination of Bollinger Bands and RSI strategy"""
        while True:
            try:
                symbol = f"NSE:{STRATEGY_CONFIG['symbol']}"
                if symbol not in self.ltpDict:
                    time.sleep(2)
                    continue

                # Get historical data (15min timeframe)
                hist_data = getHistorical(symbol, 15, 3)
                
                # Calculate indicators
                bollinger = self.calculate_bollinger_bands(hist_data)
                rsi = self.calculate_rsi(hist_data)
                current_price = self.ltpDict[symbol]

                # Generate signals
                if (current_price <= bollinger['lower'].iloc[-1]) and (rsi.iloc[-1] < 35):
                    self.execute_trade('BUY', current_price)
                elif (current_price >= bollinger['upper'].iloc[-1]) and (rsi.iloc[-1] > 65):
                    self.execute_trade('SELL', current_price)

                time.sleep(300)  # Check every 5 minutes

            except Exception as e:
                print(f"Strategy Error: {str(e)}")
                time.sleep(60)

    def execute_trade(self, direction, trigger_price):
        """Execute option trade with risk management"""
        if len(self.active_trades) >= STRATEGY_CONFIG['max_trades']:
            return

        # Get nearest expiry and strike
        expiry = getNiftyExpiryDate() if STRATEGY_CONFIG['symbol'] == 'NIFTY' else getBankNiftyExpiryDate()
        strike = self.calculate_strike(trigger_price, direction)
        
        # Create option symbol
        option_type = 'CE' if direction == 'SELL' else 'PE'
        symbol = f"NFO:{STRATEGY_CONFIG['symbol']}{expiry}{strike}{option_type}"

        # Calculate position size
        position_size = self.calculate_position_size(trigger_price)

        # Place order
        order = placeOrder(
            symbol=symbol,
            t_type='BUY',
            qty=STRATEGY_CONFIG['lot_size'] * position_size,
            order_type=STRATEGY_CONFIG['order_type'],
            price=trigger_price,
            variety='NORMAL',
            papertrading=STRATEGY_CONFIG['paper_trading']
        )
        
        if order:
            self.active_trades.append({
                'order_id': order,
                'symbol': symbol,
                'entry_price': trigger_price,
                'stop_loss': trigger_price * 0.98 if direction == 'BUY' else trigger_price * 1.02,
                'take_profit': trigger_price * 1.02 if direction == 'BUY' else trigger_price * 0.98,
                'direction': direction
            })
            print(f"Trade executed: {symbol} @ {trigger_price}")

    def calculate_strike(self, price, direction):
        """Calculate nearest option strike price"""
        multiplier = 100 if STRATEGY_CONFIG['symbol'] == 'NIFTY' else 100
        strike = round(price / multiplier) * multiplier
        return strike + (multiplier if direction == 'SELL' else -multiplier)

    def calculate_position_size(self, entry_price):
        """Calculate position size based on risk"""
        account_balance = 100000  # Replace with actual balance check
        risk_amount = STRATEGY_CONFIG['risk_per_trade'] * account_balance
        return int(risk_amount / (entry_price * STRATEGY_CONFIG['lot_size']))

    def calculate_bollinger_bands(self, data, window=20):
        """Calculate Bollinger Bands"""
        sma = data['close'].rolling(window).mean()
        std = data['close'].rolling(window).std()
        return {
            'upper': sma + (std * 2),
            'middle': sma,
            'lower': sma - (std * 2)
        }

    def calculate_rsi(self, data, window=14):
        """Calculate RSI"""
        delta = data['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs))

    def monitor_trades(self):
        """Monitor active trades and manage exits"""
        while True:
            for trade in self.active_trades.copy():
                current_price = self.ltpDict.get(trade['symbol'], None)
                
                if current_price:
                    # Check stop loss
                    if (trade['direction'] == 'BUY' and current_price <= trade['stop_loss']) or \
                       (trade['direction'] == 'SELL' and current_price >= trade['stop_loss']):
                        self.exit_trade(trade, 'SL', current_price)
                    
                    # Check take profit
                    elif (trade['direction'] == 'BUY' and current_price >= trade['take_profit']) or \
                         (trade['direction'] == 'SELL' and current_price <= trade['take_profit']):
                        self.exit_trade(trade, 'TP', current_price)

            time.sleep(5)

    def exit_trade(self, trade, reason, exit_price):
        """Exit existing trade"""
        placeOrder(
            symbol=trade['symbol'],
            t_type='SELL',
            qty=trade['qty'],
            order_type='MARKET',
            price=exit_price,
            variety='NORMAL',
            papertrading=STRATEGY_CONFIG['paper_trading']
        )
        self.active_trades.remove(trade)
        print(f"Trade exited: {trade['symbol']} @ {exit_price} ({reason})")

if __name__ == "__main__":
    strategy = AngelTradingStrategy()
    
    # Start strategy threads
    strategy_thread = threading.Thread(target=strategy.bollinger_rsi_strategy)
    monitor_thread = threading.Thread(target=strategy.monitor_trades)
    
    strategy_thread.start()
    monitor_thread.start()
    
    print("Algorithmic trading strategy is running...")