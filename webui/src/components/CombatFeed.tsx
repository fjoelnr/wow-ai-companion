import { useEffect, useRef } from "react";
import type { CombatEvent } from "../utils/types";
import { formatNumber } from "../utils/formatters";

interface CombatFeedProps {
  events: CombatEvent[];
}

const EVENT_COLORS: Record<string, string> = {
  SPELL_DAMAGE: "#ff6666",
  SPELL_PERIODIC_DAMAGE: "#cc4444",
  SWING_DAMAGE: "#ff8800",
  RANGE_DAMAGE: "#ffaa44",
  SPELL_HEAL: "#00ff88",
  SPELL_PERIODIC_HEAL: "#00cc66",
  SPELL_INTERRUPT: "#ffff00",
  SPELL_DISPEL: "#aa88ff",
  UNIT_DIED: "#ff0000",
  SPELL_CAST_SUCCESS: "#aaaaaa",
  ENCOUNTER_START: "#00aaff",
  ENCOUNTER_END: "#00aaff",
};

function getEventColor(subevent: string): string {
  return EVENT_COLORS[subevent] ?? "#666666";
}

function formatEvent(ev: CombatEvent): string {
  const amount = ev.amount ? ` (${formatNumber(ev.amount)})` : "";
  const spell = ev.spellName ? `[${ev.spellName}]` : "";

  switch (ev.subevent) {
    case "UNIT_DIED":
      return `💀 ${ev.destName} died`;
    case "SPELL_INTERRUPT":
      return `⚡ ${ev.sourceName} interrupted ${ev.destName} ${spell}`;
    case "ENCOUNTER_START":
      return `🏰 Encounter started`;
    case "ENCOUNTER_END":
      return `🏰 Encounter ended`;
    default:
      return `${ev.sourceName} → ${ev.destName} ${spell}${amount}`;
  }
}

export function CombatFeed({ events }: CombatFeedProps) {
  const bottomRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom on new events
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [events.length]);

  return (
    <div className="panel combat-feed">
      <h3>Combat Feed</h3>
      <div className="combat-feed__list">
        {events.length === 0 ? (
          <p className="panel__empty">No combat events yet...</p>
        ) : (
          events.slice(-50).map((ev, i) => (
            <div
              key={i}
              className="combat-feed__event"
              style={{ color: getEventColor(ev.subevent) }}
            >
              <span className="combat-feed__type">
                {ev.subevent.replace("SPELL_", "").replace("_", " ")}
              </span>
              <span className="combat-feed__detail">{formatEvent(ev)}</span>
            </div>
          ))
        )}
        <div ref={bottomRef} />
      </div>
    </div>
  );
}
