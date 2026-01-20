import yfinance as yf
from fastapi import FastAPI, Query, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from datetime import datetime, timedelta
import numpy as np

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Топ-25 американских компаний
COMPANIES = {
    "Apple": "AAPL",
    "Microsoft": "MSFT",
    "Nvidia": "NVDA",
    "Amazon": "AMZN",
    "Alphabet (Google)": "GOOGL",
    "Meta (Facebook)": "META",
    "Tesla": "TSLA",
    "Berkshire Hathaway": "BRK-B",
    "Visa": "V",
    "JPMorgan Chase": "JPM",
    "Walmart": "WMT",
    "Mastercard": "MA",
    "Procter & Gamble": "PG",
    "Johnson & Johnson": "JNJ",
    "Home Depot": "HD",
    "Netflix": "NFLX",
    "Bank of America": "BAC",
    "Coca-Cola": "KO",
    "Chevron": "CVX",
    "Pfizer": "PFE",
    "Intel": "INTC",
    "Nike": "NKE",
    "McDonald's": "MCD",
    "Disney": "DIS",
    "Cisco": "CSCO"
}

def get_historical_data(ticker: str, period: str = "1mo", interval: str = "1d"):
    """Получение реальных исторических данных с Yahoo Finance"""
    try:
        print(f"📥 Загрузка данных для {ticker}, период: {period}, интервал: {interval}")
        
        stock = yf.Ticker(ticker)
        hist = stock.history(period=period, interval=interval)
        
        if hist.empty:
            print(f"⚠️ Нет данных для {ticker}")
            return None
        
        result = {
            'time': [],
            'open': [],
            'high': [],
            'low': [],
            'close': [],
            'volume': []
        }
        
        for index, row in hist.iterrows():
            result['time'].append(index.strftime('%Y-%m-%d %H:%M:%S'))
            result['open'].append(float(row['Open']))
            result['high'].append(float(row['High']))
            result['low'].append(float(row['Low']))
            result['close'].append(float(row['Close']))
            result['volume'].append(float(row['Volume']))
        
        print(f"✅ Загружено {len(result['time'])} свечей с биржи")
        return result
        
    except Exception as e:
        print(f"❌ Ошибка получения данных: {e}")
        import traceback
        traceback.print_exc()
        return None

def advanced_forecast(prices, volumes=None, period_type="1mo"):
    """Продвинутый AI прогноз на основе технического анализа"""
    try:
        if len(prices) < 5:
            return [None] * len(prices), "неизвестно", 50.0
        
        # Корректировка параметров в зависимости от периода
        if period_type == "1d":
            # Краткосрочный прогноз - более чувствительный
            fast_period = min(6, len(prices) // 3)
            slow_period = min(12, len(prices) // 2)
            rsi_period = min(7, len(prices) - 1)
        elif period_type == "5d":
            # Среднесрочный прогноз
            fast_period = min(12, len(prices) // 2)
            slow_period = min(26, len(prices))
            rsi_period = min(14, len(prices) - 1)
        else:  # 1mo
            # Долгосрочный прогноз - более консервативный
            fast_period = min(20, len(prices) // 2)
            slow_period = min(50, len(prices))
            rsi_period = min(21, len(prices) - 1)
        
        def calculate_ema(data, period):
            ema = []
            multiplier = 2 / (period + 1)
            ema.append(data[0])
            for i in range(1, len(data)):
                ema.append((data[i] * multiplier) + (ema[-1] * (1 - multiplier)))
            return ema
        
        ema_fast = calculate_ema(prices, fast_period)
        ema_slow = calculate_ema(prices, slow_period)
        
        def calculate_rsi(prices, period):
            period = min(period, len(prices) - 1)
            deltas = [prices[i] - prices[i-1] for i in range(1, len(prices))]
            gains = [max(0, d) for d in deltas]
            losses = [max(0, -d) for d in deltas]
            
            avg_gain = np.mean(gains[-period:]) if len(gains) >= period else np.mean(gains) if gains else 0
            avg_loss = np.mean(losses[-period:]) if len(losses) >= period else np.mean(losses) if losses else 0
            
            if avg_loss == 0:
                return 100
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))
            return rsi
        
        rsi = calculate_rsi(prices, rsi_period)
        
        macd_line = ema_fast[-1] - ema_slow[-1] if len(ema_fast) == len(ema_slow) else 0
        
        sma = np.mean(prices[-20:]) if len(prices) >= 20 else np.mean(prices)
        std = np.std(prices[-20:]) if len(prices) >= 20 else np.std(prices)
        upper_band = sma + (2 * std)
        lower_band = sma - (2 * std)
        current_price = prices[-1]
        
        if std > 0:
            bb_position = (current_price - lower_band) / (upper_band - lower_band)
        else:
            bb_position = 0.5
        
        recent_window = min(14, len(prices))
        recent_prices = prices[-recent_window:]
        x = np.arange(recent_window)
        x_mean = np.mean(x)
        y_mean = np.mean(recent_prices)
        
        numerator = sum((x[i] - x_mean) * (recent_prices[i] - y_mean) for i in range(recent_window))
        denominator = sum((x[i] - x_mean) ** 2 for i in range(recent_window))
        slope = numerator / denominator if denominator != 0 else 0
        
        returns = [(recent_prices[i] / recent_prices[i-1] - 1) for i in range(1, len(recent_prices))]
        volatility = np.std(returns) if returns else 0
        
        volume_trend = 0
        if volumes and len(volumes) >= 10:
            recent_vol = volumes[-5:]
            prev_vol = volumes[-10:-5]
            avg_recent = np.mean(recent_vol)
            avg_prev = np.mean(prev_vol)
            if avg_prev > 0:
                volume_trend = (avg_recent / avg_prev - 1) * 100
        
        momentum_period = min(10, len(prices) - 1)
        momentum = (prices[-1] / prices[-momentum_period] - 1) * 100 if len(prices) > momentum_period else 0
        
        price_change = ((prices[-1] / prices[0]) - 1) * 100 if prices[0] > 0 else 0
        slope_pct = (slope / prices[-1]) * 100 if prices[-1] > 0 else 0
        
        # Веса индикаторов зависят от периода
        if period_type == "1d":
            # Краткосрочно больше веса на momentum и RSI
            trend_score = (
                slope_pct * 20 +
                (rsi - 50) * 0.6 +
                price_change * 0.15 +
                (macd_line / prices[-1] * 100) * 10 +
                (bb_position - 0.5) * 35 +
                momentum * 0.25 +
                volume_trend * 0.15
            )
        elif period_type == "5d":
            # Среднесрочно баланс всех индикаторов
            trend_score = (
                slope_pct * 25 +
                (rsi - 50) * 0.4 +
                price_change * 0.2 +
                (macd_line / prices[-1] * 100) * 15 +
                (bb_position - 0.5) * 40 +
                momentum * 0.15 +
                volume_trend * 0.125
            )
        else:  # 1mo
            # Долгосрочно больше веса на тренд и MACD
            trend_score = (
                slope_pct * 35 +
                (rsi - 50) * 0.25 +
                price_change * 0.3 +
                (macd_line / prices[-1] * 100) * 20 +
                (bb_position - 0.5) * 30 +
                momentum * 0.1 +
                volume_trend * 0.1
            )
        
        oversold = rsi < 30 or bb_position < 0.1
        overbought = rsi > 70 or bb_position > 0.9
        
        # Пороги тренда зависят от периода
        if period_type == "1d":
            threshold = 1.2
        elif period_type == "5d":
            threshold = 1.5
        else:
            threshold = 2.0
        
        if trend_score > threshold:
            trend = "вверх"
            base_confidence = 55 if period_type == "1d" else 60
            if overbought:
                base_confidence -= 12
        elif trend_score < -threshold:
            trend = "вниз"
            base_confidence = 55 if period_type == "1d" else 60
            if oversold:
                base_confidence -= 12
        else:
            trend = "боковой"
            base_confidence = 42 if period_type == "1d" else 45
        
        confidence = base_confidence + min(abs(trend_score) * 2, 12)
        
        # Корректировка на волатильность (зависит от периода)
        volatility_penalty = min(volatility * (60 if period_type == "1d" else 50), 25)
        confidence -= volatility_penalty
        
        if abs(volume_trend) > 20 and np.sign(volume_trend) == np.sign(trend_score):
            confidence += 3
        
        indicators_conflict = 0
        if (rsi > 70 and trend_score > 0) or (rsi < 30 and trend_score < 0):
            indicators_conflict += 8
        if abs(bb_position - 0.5) < 0.2:
            indicators_conflict += 5
        confidence -= indicators_conflict
        
        # Диапазон зависит от периода
        if period_type == "1d":
            confidence = max(25, min(78, confidence))
        elif period_type == "5d":
            confidence = max(30, min(80, confidence))
        else:
            confidence = max(35, min(75, confidence))
        
        forecast_line = []
        window = min(9, len(prices))
        for i in range(len(ema_fast)):
            if i < window - 1:
                forecast_line.append(None)
            else:
                forecast_line.append(ema_fast[i])
        
        return forecast_line, trend, round(confidence, 1)
        
    except Exception as e:
        print(f"❌ Ошибка в прогнозе: {e}")
        import traceback
        traceback.print_exc()
        return [None] * len(prices), "неизвестно", 50.0

@app.get("/")
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/get_data")
def get_data(company: str = Query(...), period: str = Query(...)):
    try:
        ticker = COMPANIES.get(company)
        if not ticker:
            return JSONResponse({"error": f"Неизвестная компания: {company}"}, status_code=400)
        
        print(f"\n{'='*70}")
        print(f"📊 Запрос: {company} ({ticker}), период: {period}")
        
        period_config = {
            "1d": {"period": "5d", "interval": "30m"},
            "5d": {"period": "1mo", "interval": "1d"},
            "1mo": {"period": "3mo", "interval": "1d"}
        }
        
        config = period_config.get(period, {"period": "1mo", "interval": "1d"})
        
        hist_data = get_historical_data(ticker, config["period"], config["interval"])
        
        if not hist_data or not hist_data['time']:
            return JSONResponse({
                "error": "Не удалось получить данные. Попробуйте другую компанию или период."
            }, status_code=400)
        
        forecast_line, trend, confidence = advanced_forecast(
            hist_data['close'],
            hist_data['volume'],
            period  # Передаем период для вариативности прогноза
        )
        
        while len(forecast_line) < len(hist_data['time']):
            forecast_line.insert(0, None)
        forecast_line = forecast_line[:len(hist_data['time'])]
        
        first_price = hist_data['close'][0]
        last_price = hist_data['close'][-1]
        change_pct = ((last_price / first_price) - 1) * 100 if first_price > 0 else 0
        
        print(f"✅ Прогноз AI: {trend.upper()} (уверенность: {confidence}%)")
        print(f"💰 Цена: ${first_price:.2f} → ${last_price:.2f}")
        print(f"📈 Изменение: {change_pct:+.2f}%")
        print(f"{'='*70}\n")
        
        return {
            "time": hist_data['time'],
            "open": hist_data['open'],
            "high": hist_data['high'],
            "low": hist_data['low'],
            "close": hist_data['close'],
            "forecast_line": forecast_line,
            "trend": trend,
            "confidence": confidence,
            "error": None
        }
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return JSONResponse({"error": f"Ошибка сервера: {str(e)}"}, status_code=500)