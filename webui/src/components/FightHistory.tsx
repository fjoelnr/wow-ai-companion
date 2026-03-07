import { useState } from "react";
import type { FightSummary } from "../utils/types";
import { formatDuration, formatNumber, formatResult, formatTime } from "../utils/formatters";

interface FightHistoryProps {
  fights: FightSummary[];
  onAnalyze?: (fight: FightSummary) => void;
}

export function FightHistory({ fights, onAnalyze }: FightHistoryProps) {
  const [expanded, setExpanded] = useState<number | null>(null);

  const reversed = [...fights].reverse();

  return (
    <div className="panel fight-history">
      <h3>Fight History ({fights.length})</h3>
      <div className="fight-history__list">
        {reversed.length === 0 ? (
          <p className="panel__empty">No fights recorded yet...</p>
        ) : (
          reversed.map((fight, idx) => {
            const { text: resultText, color: resultColor } = formatResult(fight.result);
            const isExpanded = expanded === idx;

            return (
              <div
                key={idx}
                className={`fight-history__item ${isExpanded ? "fight-history__item--expanded" : ""}`}
              >
                <div
                  className="fight-history__header"
                  onClick={() => setExpanded(isExpanded ? null : idx)}
                >
                  <span className="fight-history__name">
                    {fight.encounterName ?? "Trash / Open World"}
                  </span>
                  <span className="fight-history__meta">
                    <span style={{ color: resultColor }}>{resultText}</span>
                    {" · "}
                    {formatDuration(fight.durationSec)}
                    {" · "}
                    {formatTime(fight.start)}
                  </span>
                </div>

                {isExpanded && (
                  <div className="fight-history__details">
                    <div className="fight-history__stats">
                      <span>Total Damage: {formatNumber(fight.totalDamage)}</span>
                      <span>Total Healing: {formatNumber(fight.totalHealing)}</span>
                      <span>Players: {Object.keys(fight.players).length}</span>
                    </div>
                    <div className="fight-history__players">
                      {Object.values(fight.players)
                        .sort((a, b) => b.dps - a.dps)
                        .map((p) => (
                          <div key={p.guid} className="fight-history__player">
                            <span>{p.name}</span>
                            <span>
                              DPS: {formatNumber(p.dps)} · HPS: {formatNumber(p.hps)}
                              {p.deaths > 0 && ` · ${p.deaths} Deaths`}
                              {p.interrupts > 0 && ` · ${p.interrupts} Kicks`}
                            </span>
                          </div>
                        ))}
                    </div>
                    {onAnalyze && (
                      <button
                        className="fight-history__analyze-btn"
                        onClick={(e) => {
                          e.stopPropagation();
                          onAnalyze(fight);
                        }}
                      >
                        Analysieren
                      </button>
                    )}
                  </div>
                )}
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
