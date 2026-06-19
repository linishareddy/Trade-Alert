export interface PaperTrade {
  id: string
  parsed_signal_id: string
  broker: string
  broker_order_id: string | null
  symbol: string
  qty: number
  entry_price: number
  take_profit_price: number
  stop_loss_price: number
  exit_price: number | null
  exit_reason: 'TP_HIT' | 'SL_HIT' | 'MANUAL' | null
  pnl_pct: number | null
  pnl_dollars: number | null
  status: 'OPEN' | 'CLOSED' | 'CANCELLED'
  validation_passed: boolean
  ema9: number | null
  ema13: number | null
  ema21: number | null
  vwap: number | null
  validation_reason: string | null
  created_at: string
  closed_at: string | null
}

export interface TradeListResponse {
  total: number
  trades: PaperTrade[]
}

export interface TradeSummary {
  total_trades: number
  open_trades: number
  closed_trades: number
  avg_pnl_pct: number | null
  total_pnl_dollars: number | null
}

export interface Signal {
  id: string
  raw_alert_id: string
  action: 'BUY' | 'SELL' | 'EXIT' | 'SL_HIT' | 'SCALE_IN' | 'SCALE_OUT' | 'HOLD' | 'UPDATE'
  status: 'OPEN' | 'PARTIAL' | 'CLOSED'
  ticker: string
  contract_type: 'STOCK' | 'CALL' | 'PUT' | 'UNKNOWN'
  strike: number | null
  expiry: string | null
  entry_price: number | null
  target_price: number | null
  stop_loss: number | null
  parse_format: 'A' | 'B' | 'C' | 'D' | 'AI'
  parent_id: string | null
  created_at: string
  updated_at: string
}

export interface SignalListResponse {
  total: number
  signals: Signal[]
}

export interface HealthResponse {
  status: string
  environment: string
}

export interface ConfigUpdateRequest {
  key: string
  value: boolean | number | string
}

export interface ConfigUpdateResponse {
  key: string
  value: boolean | number | string
  config: ConfigResponse
}

export interface ConfigResetResponse {
  key: string
  config: ConfigResponse
}

export interface GroqModel {
  id: string
  name: string
  speed: 'fast' | 'medium' | 'slow'
  context_k: number
  recommended: boolean
  description: string
}

export interface ConfigResponse {
  broker: string
  alpaca_paper: boolean
  execution_enabled: boolean
  ema_vwap_enabled: boolean
  market_hours_only: boolean
  market_open: string
  market_close: string
  take_profit_pct: number
  stop_loss_pct: number
  default_qty: number
  market_data_provider: string
  ema_periods: string
  bar_lookback: number
  bar_minutes: number
  supported_contracts: string
  ai_parsing_enabled: boolean
  ai_model: string
  whatsapp_enabled: boolean
  db_host: string
  db_port: number
  db_name: string
  environment: string
}

export interface IntegrationField {
  key: string
  label: string
  value: string
  is_set: boolean
  is_overridden: boolean
  env_has_value: boolean
  sensitive: boolean
  placeholder: string
  hint: string
}

export interface IntegrationGroup {
  id: string
  name: string
  description: string
  status: 'configured' | 'partial' | 'not_configured'
  restart_required: boolean
  use_env_default: boolean
  env_configured: boolean
  fields: IntegrationField[]
}

export interface IntegrationsResponse {
  groups: IntegrationGroup[]
}

export interface IntegrationUpdateRequest {
  key: string
  value: string
}

export interface IntegrationUpdateResponse {
  key: string
  integrations: IntegrationsResponse
}

export interface IntegrationGroupUpdateRequest {
  use_env_default: boolean
}

export interface IntegrationGroupUpdateResponse {
  group_id: string
  integrations: IntegrationsResponse
}

export type NotificationType =
  | 'SIGNAL_RECEIVED'
  | 'TRADE_OPENED'
  | 'SIGNAL_SKIPPED'
  | 'TP_HIT'
  | 'SL_HIT'

export interface DerivedNotification {
  id: string
  type: NotificationType
  symbol: string
  timestamp: string
  details: Record<string, string | number | null>
}

export interface User {
  id: string
  email: string
  username: string
  role: string
  is_active: boolean
  created_at: string
}

export interface LoginRequest {
  email: string
  password: string
}

export interface TokenResponse {
  access_token: string
  token_type: string
  user: User
}
