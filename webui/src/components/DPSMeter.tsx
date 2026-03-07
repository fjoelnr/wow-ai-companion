import type { FightSummary, PlayerStats } from "../utils/types";
import { getClassColor } from "../utils/classColors";
import { formatDps } from "../utils/formatters";

interface DPSMeterProps {
  fight: FightSummary | null;
  recentFights: FightSummary[];
  /** "dps" or "hps" */
  mode?: "dps" | "hps";
}

export function DPSMeter({ fight, recentFights, mode = "dps" }: DPSMeterProps) {
  // Use active fight, or fall back to most recent completed fight
  const source = fight ?? recentFights[recentFights.length - 1];

  if (!source || Object.keys(source.players).length === 0) {
    return (
      <div className="panel dps-meter">
        <h3>{mode === "dps" ? "DPS Meter" : "HPS Meter"}</h3>
        <p className="panel__empty">Waiting for combat data...</p>
      </div>
    );
  }

  const players = Object.values(source.players);
  const sorted = [...players].sort((a, b) =>
    mode === "dps" ? b.dps - a.dps : b.hps - a.hps,
  );

  const maxValue = sorted.length > 0
    ? (mode === "dps" ? sorted[0].dps : sorted[0].hps)
    : 1;

  return (
    <div className="panel dps-meter">
      <h3>
        {mode === "dps" ? "DPS Meter" : "HPS Meter"}
        {source.encounterName && (
          <span className="dps-meter__encounter"> – {source.encounterName}</span>
        )}
      </h3>
      <div className="dps-meter__list">
        {sorted.map((p) => (
          <DPSBar key={p.guid} player={p} mode={mode} maxValue={maxValue} />
        ))}
      </div>
    </div>
  );
}

function DPSBar({
  player,
  mode,
  maxValue,
}: {
  player: PlayerStats;
  mode: "dps" | "hps";
  maxValue: number;
}) {
  const value = mode === "dps" ? player.dps : player.hps;
  const pct = maxValue > 0 ? (value / maxValue) * 100 : 0;
  const color = getClassColor(player.class);

  return (
    <div className="dps-bar">
      <div className="dps-bar__name" style={{ color }}>
        {player.name}
      </div>
      <div className="dps-bar__track">
        <div
          className="dps-bar__fill"
          style={{ width: `${pct}%`, backgroundColor: color }}
        />
      </div>
      <div className="dps-bar__value">{formatDps(value)}</div>
    </div>
  );
}
