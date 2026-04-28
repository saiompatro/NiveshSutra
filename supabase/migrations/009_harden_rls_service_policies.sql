-- Remove broad permissive "service" policies. Supabase service-role keys bypass
-- RLS already; public/authenticated roles must not inherit those privileges.

DROP POLICY IF EXISTS "Service can manage ohlcv" ON public.ohlcv;
DROP POLICY IF EXISTS "Service can manage indicators" ON public.technical_indicators;
DROP POLICY IF EXISTS "Service can manage news" ON public.news_articles;
DROP POLICY IF EXISTS "Service can manage sentiments" ON public.article_sentiments;
DROP POLICY IF EXISTS "Service can manage daily sentiment" ON public.sentiment_daily;
DROP POLICY IF EXISTS "Service can manage signal config" ON public.signal_config;
DROP POLICY IF EXISTS "Service can manage signals" ON public.signals;
DROP POLICY IF EXISTS "Service can manage optimizations" ON public.portfolio_optimizations;
DROP POLICY IF EXISTS "Service can manage allocations" ON public.optimization_allocations;
DROP POLICY IF EXISTS "Service can manage rebalance history" ON public.rebalance_history;
DROP POLICY IF EXISTS "Service can manage alerts" ON public.alerts;
DROP POLICY IF EXISTS "Service can manage accepted signals" ON public.accepted_signals;
DROP POLICY IF EXISTS "Service can manage signal notifications" ON public.signal_notifications;

-- Stock creation is routed through the authenticated API, which validates market
-- symbols and writes with the server-side service role.
DROP POLICY IF EXISTS "Authenticated users can insert stocks" ON public.stocks;

-- Allow the authenticated user flow to complete portfolio optimizations without
-- granting cross-user access.
DROP POLICY IF EXISTS "Users can update own optimizations" ON public.portfolio_optimizations;
CREATE POLICY "Users can update own optimizations"
  ON public.portfolio_optimizations
  FOR UPDATE
  TO authenticated
  USING ((SELECT auth.uid()) = user_id)
  WITH CHECK ((SELECT auth.uid()) = user_id);

DROP POLICY IF EXISTS "Users can insert own allocations" ON public.optimization_allocations;
CREATE POLICY "Users can insert own allocations"
  ON public.optimization_allocations
  FOR INSERT
  TO authenticated
  WITH CHECK (
    optimization_id IN (
      SELECT id
      FROM public.portfolio_optimizations
      WHERE user_id = (SELECT auth.uid())
    )
  );
