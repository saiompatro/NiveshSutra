-- Migration 007: Signal tracking, notifications, and expanded risk profiles
-- Adds: accepted_signals table, signal_notifications table, expanded profile columns

-- ── Expanded risk profile columns ──────────────────────────────────────
ALTER TABLE public.profiles
  ADD COLUMN IF NOT EXISTS volatility_tolerance INTEGER,
  ADD COLUMN IF NOT EXISTS time_horizon_score INTEGER,
  ADD COLUMN IF NOT EXISTS knowledge_score INTEGER,
  ADD COLUMN IF NOT EXISTS investable_surplus_range TEXT,
  ADD COLUMN IF NOT EXISTS email_notifications_enabled BOOLEAN DEFAULT FALSE;

-- ── Accepted signals ───────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS public.accepted_signals (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
  symbol TEXT NOT NULL REFERENCES public.stocks(symbol),
  signal_type TEXT NOT NULL CHECK (signal_type IN ('strong_buy', 'buy', 'hold', 'sell', 'strong_sell')),
  signal_date DATE NOT NULL,
  composite_score NUMERIC,
  status TEXT DEFAULT 'active' CHECK (status IN ('active', 'executed', 'cancelled')),
  accepted_at TIMESTAMPTZ DEFAULT NOW(),
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_accepted_signals_user ON public.accepted_signals(user_id, status);
CREATE INDEX IF NOT EXISTS idx_accepted_signals_symbol ON public.accepted_signals(symbol);

ALTER TABLE public.accepted_signals ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can read own accepted signals"
  ON public.accepted_signals FOR SELECT
  USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own accepted signals"
  ON public.accepted_signals FOR INSERT
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own accepted signals"
  ON public.accepted_signals FOR UPDATE
  USING (auth.uid() = user_id);

CREATE POLICY "Service can manage accepted signals"
  ON public.accepted_signals FOR ALL
  USING (true) WITH CHECK (true);

-- ── Signal notification tracking ───────────────────────────────────────
CREATE TABLE IF NOT EXISTS public.signal_notifications (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
  symbol TEXT NOT NULL REFERENCES public.stocks(symbol),
  last_signal TEXT,
  last_notified_at TIMESTAMPTZ,
  is_active BOOLEAN DEFAULT TRUE,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(user_id, symbol)
);

CREATE INDEX IF NOT EXISTS idx_signal_notifications_active
  ON public.signal_notifications(user_id, is_active) WHERE is_active = TRUE;

ALTER TABLE public.signal_notifications ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can read own signal notifications"
  ON public.signal_notifications FOR SELECT
  USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own signal notifications"
  ON public.signal_notifications FOR INSERT
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own signal notifications"
  ON public.signal_notifications FOR UPDATE
  USING (auth.uid() = user_id);

CREATE POLICY "Service can manage signal notifications"
  ON public.signal_notifications FOR ALL
  USING (true) WITH CHECK (true);
