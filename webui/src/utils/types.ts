/** Core TypeScript types for the WoW AI Companion dashboard. */

// ── Combat Events ──────────────────────────────────────────────────────

export interface CombatEvent {
  ts: number;
  subevent: string;
  sourceName: string;
  destName: string;
  spellId: number | null;
  spellName: string | null;
  amount: number | null;
  extra: Record<string, unknown>;
}

// ── Player Stats ───────────────────────────────────────────────────────

export interface SpellUsage {
  spellId: number;
  spellName: string;
  casts: number;
  totalAmount: number;
}

export interface PlayerStats {
  guid: string;
  name: string;
  class: string;
  damageDone: number;
  healingDone: number;
  damageTaken: number;
  deaths: number;
  interrupts: number;
  dispels: number;
  dps: number;
  hps: number;
  topSpells: SpellUsage[];
}

// ── Fight Summary ──────────────────────────────────────────────────────

export interface FightSummary {
  encounterId: number | null;
  encounterName: string | null;
  start: number;
  end: number;
  durationSec: number;
  result: "kill" | "wipe" | "unknown";
  totalDamage: number;
  totalHealing: number;
  players: Record<string, PlayerStats>;
}

// ── Session Data ───────────────────────────────────────────────────────

export interface SessionData {
  ts?: number;
  player?: string;
  class?: string;
  specId?: number;
  zone?: string;
  level?: number;
  ilvl?: number;
  locale?: string;
  location?: {
    mapId: number | null;
    mapName: string | null;
    zone: string;
    subZone: string;
  };
  activeQuests?: Array<{
    id: number;
    title: string;
    isComplete: boolean;
  }>;
  professions?: Array<{
    name: string;
    skillLevel: number;
    maxLevel: number;
  }>;
}

// ── Fight Analysis ────────────────────────────────────────────────────

export interface FightAnalysis {
  summary: string;
  rating: string;
  highlights: string[];
  improvements: string[];
  tips: string[];
  fight?: FightSummary;
}

// ── WebSocket Messages ─────────────────────────────────────────────────

export type WSMessage =
  | { type: "init"; data: { session: SessionData; recentFights: FightSummary[]; wsClients: number } }
  | { type: "combat_event"; data: CombatEvent }
  | { type: "fight_end"; data: FightSummary }
  | { type: "fight_analysis"; data: FightAnalysis }
  | { type: "session_update"; data: SessionData }
  | { type: "pong"; ts: number };

// ── Dashboard State ────────────────────────────────────────────────────

export type ConnectionStatus = "connecting" | "connected" | "disconnected";

export interface DashboardState {
  connection: ConnectionStatus;
  session: SessionData | null;
  combatEvents: CombatEvent[];
  fightHistory: FightSummary[];
  activeFight: FightSummary | null;
  latestAnalysis: FightAnalysis | null;
  analysisLoading: boolean;
  inCombat: boolean;
}
