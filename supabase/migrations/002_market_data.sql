-- OHLCV table for historical price data
CREATE TABLE public.ohlcv (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  symbol TEXT NOT NULL REFERENCES public.stocks(symbol),
  date DATE NOT NULL,
  open NUMERIC,
  high NUMERIC,
  low NUMERIC,
  close NUMERIC NOT NULL,
  adj_close NUMERIC,
  volume BIGINT DEFAULT 0,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(symbol, date)
);

CREATE INDEX idx_ohlcv_symbol_date ON public.ohlcv(symbol, date DESC);

-- Technical indicators table
CREATE TABLE public.technical_indicators (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  symbol TEXT NOT NULL REFERENCES public.stocks(symbol),
  date DATE NOT NULL,
  rsi_14 NUMERIC,
  macd_line NUMERIC,
  macd_signal NUMERIC,
  macd_hist NUMERIC,
  bb_upper NUMERIC,
  bb_middle NUMERIC,
  bb_lower NUMERIC,
  sma_20 NUMERIC,
  sma_50 NUMERIC,
  ema_12 NUMERIC,
  ema_26 NUMERIC,
  atr_14 NUMERIC,
  obv NUMERIC,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(symbol, date)
);

CREATE INDEX idx_indicators_symbol_date ON public.technical_indicators(symbol, date DESC);

-- RLS
ALTER TABLE public.ohlcv ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.technical_indicators ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Anyone can read ohlcv" ON public.ohlcv FOR SELECT USING (true);
CREATE POLICY "Anyone can read indicators" ON public.technical_indicators FOR SELECT USING (true);

-- Service role can insert/update (for ML pipeline)
CREATE POLICY "Service can manage ohlcv" ON public.ohlcv FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Service can manage indicators" ON public.technical_indicators FOR ALL USING (true) WITH CHECK (true);
