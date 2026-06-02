import ccxt
import pandas as pd
import time
import os
from datetime import datetime, timedelta
import pytz

# ==================== 配置 ====================
SYMBOL = 'SOL/USDT:USDT'  # OKX 永续合约
TIMEFRAMES = ['3m', '5m', '15m', '30m', '1h', '2h', '4h', '12h', '1d']
DAYS_BACK = 90
DATA_DIR = 'data'

# 创建目录
os.makedirs(DATA_DIR, exist_ok=True)

# 北京时间 (UTC+8)
BEIJING_TZ = pytz.timezone('Asia/Shanghai')

# ==================== 初始化交易所 ====================
exchange = ccxt.okx({
    'enableRateLimit': True,        # 开启内置限速
    'options': {
        'defaultType': 'swap',      # 永续合约
    },
    # 可选：增加请求间隔，降低被封风险
    'rateLimit': 120,               # 毫秒，每请求至少间隔120ms
})

print(f"开始下载 OKX {SYMBOL} 永续合约数据（最近 {DAYS_BACK} 天）...")

def fetch_ohlcv_safe(symbol, timeframe, since=None, limit=300):
    """带重试和延时的安全下载函数"""
    for attempt in range(5):  # 最多重试5次
        try:
            ohlcv = exchange.fetch_ohlcv(symbol, timeframe, since=since, limit=limit)
            if len(ohlcv) > 0:
                time.sleep(0.15)   # 主动增加间隔，防止被封
                return ohlcv
            else:
                print(f"  {timeframe} 返回空数据，等待后重试...")
        except Exception as e:
            print(f"  下载出错 ({timeframe}): {e}")
            if "429" in str(e) or "rate limit" in str(e).lower():
                print("  触发频率限制，延长等待...")
                time.sleep(3)
            else:
                time.sleep(2 ** attempt)  # 指数退避
    return []


def download_timeframe(timeframe):
    print(f"\n正在下载 {timeframe} 数据...")

    all_data = []
    end_time = datetime.now(BEIJING_TZ)
    start_time = end_time - timedelta(days=DAYS_BACK)
    
    since = int(start_time.timestamp() * 1000)  # 转换为毫秒时间戳
    
    while True:
        ohlcv = fetch_ohlcv_safe(SYMBOL, timeframe, since=since)
        
        if len(ohlcv) == 0:
            break
            
        all_data.extend(ohlcv)
        
        # 更新 since 为最后一条数据的时间 + 1
        last_timestamp = ohlcv[-1][0]
        since = last_timestamp + 1
        
        # 如果返回数据少于 limit，说明已到最新
        if len(ohlcv) < 200:
            break
            
        time.sleep(0.2)

    if not all_data:
        print(f"  {timeframe} 未获取到任何数据")
        return

    # 转换为 DataFrame
    df = pd.DataFrame(all_data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    
    # 转换时间戳为北京时间
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    df['timestamp'] = df['timestamp'].dt.tz_localize('UTC').dt.tz_convert(BEIJING_TZ)
    
    # 去重并排序
    df = df.drop_duplicates(subset='timestamp').sort_values('timestamp').reset_index(drop=True)
    
    # 数据质量检查
    print(f"  下载完成：{len(df)} 条记录")
    print(f"  时间范围：{df['timestamp'].iloc[0]} → {df['timestamp'].iloc[-1]}")
    
    # 检查缺失值
    missing = df.isnull().sum().sum()
    if missing > 0:
        print(f"  发现 {missing} 个缺失值，已填充")
        df = df.fillna(method='ffill')
    
    # 保存为 CSV
    filename = f"{DATA_DIR}/SOL_{timeframe}_OKX.csv"
    df.to_csv(filename, index=False, encoding='utf-8')
    print(f"  已保存 → {filename}")


# ==================== 执行下载 ====================
if __name__ == "__main__":
    start_total = time.time()
    
    for tf in TIMEFRAMES:
        download_timeframe(tf)
    
    total_time = time.time() - start_total
    print(f"\n✅ 全部数据下载完成！总耗时: {total_time/60:.1f} 分钟")
    print(f"数据已保存至 `{DATA_DIR}/` 目录")
