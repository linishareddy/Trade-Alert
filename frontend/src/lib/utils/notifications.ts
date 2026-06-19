import type { PaperTrade, Signal, DerivedNotification } from '@/types'

export function deriveNotifications(
  trades: PaperTrade[],
  signals: Signal[]
): DerivedNotification[] {
  const notifications: DerivedNotification[] = []

  // Signal Received — every BUY STOCK/UNKNOWN signal
  const executableSignals = signals.filter(
    (s) => s.action === 'BUY' && (s.contract_type === 'STOCK' || s.contract_type === 'UNKNOWN')
  )
  for (const sig of executableSignals) {
    notifications.push({
      id: `sig-recv-${sig.id}`,
      type: 'SIGNAL_RECEIVED',
      symbol: sig.ticker,
      timestamp: sig.created_at,
      details: {
        action: sig.action,
        entry_price: sig.entry_price,
        stop_loss: sig.stop_loss,
      },
    })
  }

  for (const trade of trades) {
    if (trade.status === 'OPEN' && trade.validation_passed) {
      notifications.push({
        id: `trade-open-${trade.id}`,
        type: 'TRADE_OPENED',
        symbol: trade.symbol,
        timestamp: trade.created_at,
        details: {
          entry_price: trade.entry_price,
          take_profit_price: trade.take_profit_price,
          stop_loss_price: trade.stop_loss_price,
          qty: trade.qty,
          broker: trade.broker,
          ema9: trade.ema9,
          ema13: trade.ema13,
          ema21: trade.ema21,
          vwap: trade.vwap,
        },
      })
    }

    if (trade.status === 'CANCELLED' && !trade.validation_passed) {
      notifications.push({
        id: `trade-skip-${trade.id}`,
        type: 'SIGNAL_SKIPPED',
        symbol: trade.symbol,
        timestamp: trade.created_at,
        details: {
          validation_reason: trade.validation_reason,
          entry_price: trade.entry_price,
        },
      })
    }

    if (trade.status === 'CLOSED' && trade.exit_reason === 'TP_HIT') {
      notifications.push({
        id: `trade-tp-${trade.id}`,
        type: 'TP_HIT',
        symbol: trade.symbol,
        timestamp: trade.closed_at ?? trade.created_at,
        details: {
          entry_price: trade.entry_price,
          exit_price: trade.exit_price,
          pnl_pct: trade.pnl_pct,
          pnl_dollars: trade.pnl_dollars,
        },
      })
    }

    if (trade.status === 'CLOSED' && trade.exit_reason === 'SL_HIT') {
      notifications.push({
        id: `trade-sl-${trade.id}`,
        type: 'SL_HIT',
        symbol: trade.symbol,
        timestamp: trade.closed_at ?? trade.created_at,
        details: {
          entry_price: trade.entry_price,
          exit_price: trade.exit_price,
          pnl_pct: trade.pnl_pct,
          pnl_dollars: trade.pnl_dollars,
        },
      })
    }
  }

  return notifications.sort(
    (a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
  )
}
