CREATE TABLE public.signal_config (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name TEXT NOT NULL UNIQUE,
  technical_weight NUMERIC DEFAULT 0.4,
  sentiment_weight NUMERIC DEFAULT 0.3,
  momentum_weight NUMERIC DEFAULT 0.3,
  is_active BOOLEAN DEFAULT TRUE,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Insert default config
INSERT INTO public.signal_config (name, technical_weight, sentiment_weight, momentum_weight, is_active)
VALUES ('default', 0.4, 0.3, 0.3, true);

CREATE TABLE public.signals (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  symbol TEXT NOT NULL REFERENCES public.stocks(symbol),
  date DATE NOT NULL,
  technical_score NUMERIC,
  sentiment_score NUMERIC,
  momentum_score NUMERIC,
  composite_score NUMERIC,
  signal TEXT CHECK (signal IN ('strong_buy', 'buy', 'hold', 'sell', 'strong_sell')),
  confidence NUMERIC,
  explanation TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(symbol, date)
);

CREATE INDEX idx_signals_symbol_date ON public.signals(symbol, date DESC);
CREATE INDEX idx_signals_signal ON public.signals(signal);

ALTER TABLE public.signal_config ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.signals ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Anyone can read signal config" ON public.signal_config FOR SELECT USING (true);
CREATE POLICY "Anyone can read signals" ON public.signals FOR SELECT USING (true);
CREATE POLICY "Service can manage signal config" ON public.signal_config FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Service can manage signals" ON public.signals FOR ALL USING (true) WITH CHECK (true);
