import MetaTrader5 as mt5
import pandas as pd
import numpy as np
import time

# Pengaturan akun FBS
AKUN = "100580499"
PASSWORD = "m^In^4HK"
SERVER = "FBS-Demo"

# Pengaturan simbol dan timeframe
SYMBOL = "EURUSD"
TIMEFRAME = mt5.TIMEFRAME_M1
LOT_SIZE = 0.1
DEVIATION = 20

# Fungsi inisialisasi MT5
def initialize_mt5():
    if not mt5.initialize():
        print(f"MT5 initialization failed: {mt5.last_error()}")
        return False
    if not mt5.login(AKUN, PASSWORD, SERVER):
        print(f"Login failed: {mt5.last_error()}")
        mt5.shutdown()
        return False
    print("MT5 initialized and logged in successfully")
    return True

# Fungsi untuk mengambil data historis
def get_data(symbol, timeframe, n_bars=200):
    rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, n_bars)
    if rates is None:
        print(f"Failed to get rates: {mt5.last_error()}")
        return None
    df = pd.DataFrame(rates)
    df['time'] = pd.to_datetime(df['time'], unit='s')  # Konversi waktu ke datetime
    return df

# Fungsi analisis teknikal
def analisis_teknikal(df):
    # Validasi data
    if df is None or len(df) < 200:
        print("Insufficient data for analysis")
        return None
    
    # Moving Average
    df['MA_50'] = df['close'].rolling(window=50).mean()
    df['MA_200'] = df['close'].rolling(window=200).mean()

    # RSI
    delta = df['close'].diff()
    gain = np.where(delta > 0, delta, 0)
    loss = np.where(delta < 0, -delta, 0)
    avg_gain = pd.Series(gain).rolling(window=14).mean()
    avg_loss = pd.Series(loss).rolling(window=14).mean()
    rs = avg_gain / avg_loss
    df['RSI'] = 100 - (100 / (1 + rs))

    # Sinyal beli atau jual
    if df['MA_50'].iloc[-1] > df['MA_200'].iloc[-1] and df['RSI'].iloc[-1] < 30:
        return "buy"
    elif df['MA_50'].iloc[-1] < df['MA_200'].iloc[-1] and df['RSI'].iloc[-1] > 70:
        return "sell"
    return None

# Fungsi untuk mengirim order
def send_order(order_type):
    tick = mt5.symbol_info_tick(SYMBOL)
    if tick is None:
        print(f"Failed to get tick info: {mt5.last_error()}")
        return False

    price = tick.bid if order_type == mt5.ORDER_TYPE_BUY else tick.ask
    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": SYMBOL,
        "volume": LOT_SIZE,
        "type": order_type,
        "price": price,
        "deviation": DEVIATION,
        "magic": 234000,
        "comment": "Robot Trading",
        "type_time": mt5.ORDER_TIME_GTC
    }

    result = mt5.order_send(request)
    if result.retcode != mt5.TRADE_RETCODE_DONE:
        print(f"Order failed: {result.comment}")
        return False

    print(f"Order {order_type} sent successfully")
    return True

# Fungsi utama eksekusi trading
def eksekusi_trade():
    df = get_data(SYMBOL, TIMEFRAME)
    sinyal = analisis_teknikal(df)
    if sinyal == "buy":
        send_order(mt5.ORDER_TYPE_BUY)
    elif sinyal == "sell":
        send_order(mt5.ORDER_TYPE_SELL)

# Main program
if __name__ == "__main__":
    if not initialize_mt5():
        exit()

    try:
        while True:
            eksekusi_trade()
            time.sleep(60)  # Tunggu 1 menit sebelum eksekusi berikutnya
    except KeyboardInterrupt:
        print("Trading stopped manually")
    finally:
        mt5.shutdown()
        
