CREATE TABLE public.alerts (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
  alert_type TEXT NOT NULL CHECK (alert_type IN ('signal_change', 'sentiment_shift', 'rebalance_drift', 'price_alert')),
  title TEXT NOT NULL,
  message TEXT,
  symbol TEXT REFERENCES public.stocks(symbol),
  is_read BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_alerts_user_unread ON public.alerts(user_id, is_read) WHERE NOT is_read;

ALTER TABLE public.alerts ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can read own alerts" ON public.alerts FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users can update own alerts" ON public.alerts FOR UPDATE USING (auth.uid() = user_id);
CREATE POLICY "Service can manage alerts" ON public.alerts FOR ALL USING (true) WITH CHECK (true);
