CREATE TABLE public.portfolio_optimizations (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
  risk_profile TEXT,
  optimization_method TEXT,
  target_return NUMERIC,
  target_risk NUMERIC,
  expected_return NUMERIC,
  expected_risk NUMERIC,
  sharpe_ratio NUMERIC,
  status TEXT DEFAULT 'pending',
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE public.optimization_allocations (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  optimization_id UUID NOT NULL REFERENCES public.portfolio_optimizations(id) ON DELETE CASCADE,
  symbol TEXT NOT NULL REFERENCES public.stocks(symbol),
  current_weight NUMERIC,
  recommended_weight NUMERIC,
  current_value NUMERIC,
  recommended_value NUMERIC,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE public.rebalance_history (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
  optimization_id UUID REFERENCES public.portfolio_optimizations(id),
  symbol TEXT NOT NULL REFERENCES public.stocks(symbol),
  action TEXT CHECK (action IN ('buy', 'sell', 'hold')),
  quantity NUMERIC,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE public.portfolio_optimizations ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.optimization_allocations ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.rebalance_history ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can read own optimizations" ON public.portfolio_optimizations FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users can insert own optimizations" ON public.portfolio_optimizations FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "Service can manage optimizations" ON public.portfolio_optimizations FOR ALL USING (true) WITH CHECK (true);

CREATE POLICY "Users can read own allocations" ON public.optimization_allocations FOR SELECT USING (
  optimization_id IN (SELECT id FROM public.portfolio_optimizations WHERE user_id = auth.uid())
);
CREATE POLICY "Service can manage allocations" ON public.optimization_allocations FOR ALL USING (true) WITH CHECK (true);

CREATE POLICY "Users can read own rebalance history" ON public.rebalance_history FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Service can manage rebalance history" ON public.rebalance_history FOR ALL USING (true) WITH CHECK (true);
