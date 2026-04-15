CREATE TABLE public.news_articles (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  url TEXT NOT NULL UNIQUE,
  title TEXT NOT NULL,
  source TEXT,
  published_at TIMESTAMPTZ,
  fetched_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE public.article_sentiments (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  article_id UUID NOT NULL REFERENCES public.news_articles(id) ON DELETE CASCADE,
  symbol TEXT NOT NULL REFERENCES public.stocks(symbol),
  positive_prob NUMERIC,
  negative_prob NUMERIC,
  neutral_prob NUMERIC,
  sentiment_label TEXT,
  relevance_score NUMERIC DEFAULT 1.0,
  computed_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(article_id, symbol)
);

CREATE TABLE public.sentiment_daily (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  symbol TEXT NOT NULL REFERENCES public.stocks(symbol),
  date DATE NOT NULL,
  avg_sentiment NUMERIC,
  positive_avg NUMERIC,
  negative_avg NUMERIC,
  neutral_avg NUMERIC,
  article_count INTEGER DEFAULT 0,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(symbol, date)
);

CREATE INDEX idx_sentiment_daily_symbol_date ON public.sentiment_daily(symbol, date DESC);

ALTER TABLE public.news_articles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.article_sentiments ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.sentiment_daily ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Anyone can read news" ON public.news_articles FOR SELECT USING (true);
CREATE POLICY "Service can manage news" ON public.news_articles FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Anyone can read sentiments" ON public.article_sentiments FOR SELECT USING (true);
CREATE POLICY "Service can manage sentiments" ON public.article_sentiments FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Anyone can read daily sentiment" ON public.sentiment_daily FOR SELECT USING (true);
CREATE POLICY "Service can manage daily sentiment" ON public.sentiment_daily FOR ALL USING (true) WITH CHECK (true);
