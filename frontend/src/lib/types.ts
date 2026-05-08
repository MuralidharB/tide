// Mirrors backend/tide/api/schemas.py — keep in sync.

export type SignClass = 'pos' | 'neg' | 'neu';
export type VoteDirection = 'bull' | 'bear' | 'neutral';

export interface Vote {
  direction: VoteDirection;
  reason: string;
}

export interface Reading {
  metric_id: string;
  name: string;
  tier: number;
  source: string;
  unit: string;
  value: string;
  delta: string;
  delta_class: SignClass;
  z: number;
  z_label: string;
  z_class: SignClass;
  as_of: string; // ISO date
  sparkline: number[];
  vote: Vote;
}

export interface Tier {
  tier: number;
  name: string;
  tag: string;
  cadence: string;
  metrics: Reading[];
  avg_z: number | null;
}

export interface Tally {
  bull: number;
  neutral: number;
  bear: number;
}

export interface Composite {
  z: number;
  z_label: string;
  sign_class: SignClass;
  tally: Tally;
  metrics_total: number;
}

export interface CompositeHistoryPoint {
  ts: string;
  z: number;
}

export interface Dashboard {
  composite: Composite | null;
  tiers: Tier[];
  composite_history: CompositeHistoryPoint[];
}

export interface WatchlistRow {
  ticker: string;
  name: string;
  sub: string;
  price: number | null;
  target: number;
  fwd_pe: string;
  status: 'watching' | 'starter' | 'building';
  return_30d: number | null;
  return_30d_relative: number | null;
  sparkline: number[];
  as_of: string | null;
}

export interface Watchlist {
  rows: WatchlistRow[];
  benchmark: string;
}

export interface SourceRow {
  metric_id: string;
  name: string;
  tier: number;
  source: string;
  source_kind: string;
  cadence: string;
  status: 'live' | 'stub';
  last_observation: string | null;
  last_ingested_at: string | null;
  obs_count: number;
}

export interface SourcesPayload {
  rows: SourceRow[];
}
