export type SignalLabel =
  | "strong_buy"
  | "buy"
  | "hold"
  | "sell"
  | "strong_sell";

export interface Quote {
  symbol: string;
  price: number;
  previous_close: number;
  change: number;
  change_pct: number;
  open: number;
  high: number;
  low: number;
  volume: number;
  latest_trading_day: string;
  provider: string;
}

export interface Signal {
  symbol: string;
  date: string;
  signal: SignalLabel;
  composite_score: number;
  technical_score: number;
  sentiment_score: number;
  momentum_score: number;
  confidence: number;
  explanation: string;
}

export interface Holding {
  id: string;
  symbol: string;
  quantity: number;
  avg_price: number;
  current_price: number;
  pnl: number;
  pnl_pct: number;
  value: number;
  provider: string;
}

export interface NiftyIndex {
  nifty50_value: number;
  nifty50_change: number;
  nifty50_change_pct: number;
  provider: string;
}

export interface Alert {
  id: string;
  alert_type: string;
  title: string;
  message: string;
  symbol: string | null;
  is_read: boolean;
  created_at: string;
}
