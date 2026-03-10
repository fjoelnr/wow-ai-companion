import type { PlayerStats } from "../utils/types";
import { formatNumber } from "../utils/formatters";
import { getClassColor } from "../utils/classColors";

interface SpellBreakdownProps {
  players: Record<string, PlayerStats>;
}

export function SpellBreakdown({ players }: SpellBreakdownProps) {
  const sorted = Object.values(players).sort((a, b) => b.dps - a.dps);

  return (
    <div className="spell-breakdown">
      {sorted.map((player) => (
        <div key={player.guid} className="spell-breakdown__player">
          <div
            className="spell-breakdown__player-header"
            style={{ borderLeftColor: getClassColor(player.class) }}
          >
            <span className="spell-breakdown__name">{player.name}</span>
            <span className="spell-breakdown__meta">
              {formatNumber(player.dps)} DPS · {formatNumber(player.hps)} HPS
              {player.deaths > 0 && <span className="spell-breakdown__deaths"> · {player.deaths} Deaths</span>}
              {player.interrupts > 0 && <span className="spell-breakdown__interrupts"> · {player.interrupts} Kicks</span>}
              {player.dispels > 0 && <span className="spell-breakdown__dispels"> · {player.dispels} Dispels</span>}
            </span>
          </div>

          {player.topSpells && player.topSpells.length > 0 && (
            <div className="spell-breakdown__spells">
              {player.topSpells.map((spell) => {
                const maxAmount = player.topSpells[0]?.totalAmount ?? 1;
                const pct = maxAmount > 0 ? (spell.totalAmount / maxAmount) * 100 : 0;

                return (
                  <div key={spell.spellId} className="spell-breakdown__spell">
                    <span className="spell-breakdown__spell-name">
                      {spell.spellName}
                    </span>
                    <div className="spell-breakdown__spell-bar-track">
                      <div
                        className="spell-breakdown__spell-bar-fill"
                        style={{
                          width: `${pct}%`,
                          backgroundColor: getClassColor(player.class),
                        }}
                      />
                    </div>
                    <span className="spell-breakdown__spell-stats">
                      {spell.casts}x · {formatNumber(spell.totalAmount)}
                    </span>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      ))}
    </div>
  );
}
