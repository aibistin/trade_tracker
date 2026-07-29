/**
 * syncEvents.js
 * Minimal pub/sub so components can react to a completed Schwab sync
 * without a global state store (this app has none — state is
 * router-based or component-local).
 */
const listeners = new Set()

export function onSyncComplete(callback) {
  listeners.add(callback)
  return () => listeners.delete(callback)
}

export function emitSyncComplete(symbol) {
  listeners.forEach((callback) => callback(symbol))
}
