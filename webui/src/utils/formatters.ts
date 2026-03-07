/** Formatting helpers for numbers, time, and WoW-specific data. */

/** Format large numbers with K/M suffixes: 1234567 → "1.23M" */
export function formatNumber(n: number): string {
  if (n >= 1_000_000) return (n / 1_000_000).toFixed(2) + "M";
  if (n >= 1_000) return (n / 1_000).toFixed(1) + "K";
  return n.toFixed(0);
}

/** Format DPS/HPS: 12345.6 → "12.3K" */
export function formatDps(n: number): string {
  if (n >= 1_000_000) return (n / 1_000_000).toFixed(1) + "M";
  if (n >= 1_000) return (n / 1_000).toFixed(1) + "K";
  return n.toFixed(0);
}

/** Format seconds to mm:ss: 185 → "3:05" */
export function formatDuration(seconds: number): string {
  const m = Math.floor(seconds / 60);
  const s = Math.floor(seconds % 60);
  return `${m}:${s.toString().padStart(2, "0")}`;
}

/** Format Unix timestamp to HH:MM:SS */
export function formatTime(ts: number): string {
  const d = new Date(ts * 1000);
  return d.toLocaleTimeString("de-DE", { hour: "2-digit", minute: "2-digit", second: "2-digit" });
}

/** Format gold from copper: 1234567 → "123g 45s 67c" */
export function formatGold(copper: number): string {
  const gold = Math.floor(copper / 10000);
  const silver = Math.floor((copper % 10000) / 100);
  const cop = copper % 100;
  return `${gold}g ${silver}s ${cop}c`;
}

/** Get a human-readable fight result. */
export function formatResult(result: string): { text: string; color: string } {
  switch (result) {
    case "kill":
      return { text: "Kill", color: "#00ff88" };
    case "wipe":
      return { text: "Wipe", color: "#ff4444" };
    default:
      return { text: "—", color: "#888888" };
  }
}
