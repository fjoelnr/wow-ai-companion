import { useState } from "react";
import type { FightAnalysis as FightAnalysisData, FightSummary } from "../utils/types";
import { formatDuration, formatNumber, formatResult } from "../utils/formatters";
import { SpellBreakdown } from "./SpellBreakdown";

interface FightAnalysisProps {
  analysis: FightAnalysisData | null;
  loading: boolean;
  activeFight: FightSummary | null;
  onAnalyze: (fight: FightSummary) => void;
  onDismiss: () => void;
}

const RATING_COLORS: Record<string, string> = {
  S: "#ffcc00",
  A: "#00ff88",
  B: "#00aaff",
  C: "#aa66ff",
  D: "#ff8844",
  F: "#ff4444",
  "?": "#888899",
};

function RatingBadge({ rating }: { rating: string }) {
  const color = RATING_COLORS[rating.toUpperCase()] ?? RATING_COLORS["?"];
  return (
    <span className="analysis__rating" style={{ borderColor: color, color }}>
      {rating}
    </span>
  );
}

export function FightAnalysis({
  analysis,
  loading,
  activeFight,
  onAnalyze,
  onDismiss,
}: FightAnalysisProps) {
  const [showSpells, setShowSpells] = useState(false);

  // Show fight info when there's an active fight but no analysis yet
  if (!analysis && activeFight && !loading) {
    const { text: resultText, color: resultColor } = formatResult(activeFight.result);
    return (
      <div className="panel analysis">
        <h3>
          Kampf-Coach
        </h3>
        <div className="analysis__pending">
          <div className="analysis__fight-info">
            <span className="analysis__encounter">
              {activeFight.encounterName ?? "Trash / Open World"}
            </span>
            <span className="analysis__fight-meta">
              <span style={{ color: resultColor }}>{resultText}</span>
              {" · "}
              {formatDuration(activeFight.durationSec)}
              {" · "}
              {Object.keys(activeFight.players).length} Spieler
            </span>
          </div>
          <button
            className="analysis__btn analysis__btn--analyze"
            onClick={() => onAnalyze(activeFight)}
          >
            Kampf analysieren
          </button>
          <button
            className="analysis__btn analysis__btn--dismiss"
            onClick={onDismiss}
          >
            Schließen
          </button>
        </div>
      </div>
    );
  }

  // Loading state
  if (loading) {
    return (
      <div className="panel analysis">
        <h3>Kampf-Coach</h3>
        <div className="analysis__loading">
          <div className="analysis__spinner" />
          <span>LLM analysiert den Kampf...</span>
        </div>
      </div>
    );
  }

  // No analysis at all
  if (!analysis) {
    return (
      <div className="panel analysis">
        <h3>Kampf-Coach</h3>
        <p className="panel__empty">
          Beende einen Kampf, um eine Analyse zu erhalten...
        </p>
      </div>
    );
  }

  // Full analysis display
  const fight = analysis.fight;

  return (
    <div className="panel analysis">
      <h3>
        Kampf-Coach
        <RatingBadge rating={analysis.rating} />
        {fight && (
          <span className="analysis__encounter-tag">
            {fight.encounterName ?? "Trash"}
          </span>
        )}
      </h3>

      <div className="analysis__content">
        {/* Summary */}
        <div className="analysis__summary">{analysis.summary}</div>

        {/* Fight stats row */}
        {fight && (
          <div className="analysis__stats-row">
            <span>
              <span style={{ color: formatResult(fight.result).color }}>
                {formatResult(fight.result).text}
              </span>
            </span>
            <span>{formatDuration(fight.durationSec)}</span>
            <span>Dmg: {formatNumber(fight.totalDamage)}</span>
            <span>Heal: {formatNumber(fight.totalHealing)}</span>
          </div>
        )}

        {/* Highlights */}
        {analysis.highlights && analysis.highlights.length > 0 && (
          <div className="analysis__section">
            <h4 className="analysis__section-title analysis__section-title--good">
              Highlights
            </h4>
            <ul className="analysis__list">
              {analysis.highlights.map((h, i) => (
                <li key={i} className="analysis__item analysis__item--good">
                  {h}
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Improvements */}
        {analysis.improvements && analysis.improvements.length > 0 && (
          <div className="analysis__section">
            <h4 className="analysis__section-title analysis__section-title--warn">
              Verbesserungen
            </h4>
            <ul className="analysis__list">
              {analysis.improvements.map((imp, i) => (
                <li key={i} className="analysis__item analysis__item--warn">
                  {imp}
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Tips */}
        {analysis.tips && analysis.tips.length > 0 && (
          <div className="analysis__section">
            <h4 className="analysis__section-title analysis__section-title--tip">
              Tipps
            </h4>
            <ul className="analysis__list">
              {analysis.tips.map((tip, i) => (
                <li key={i} className="analysis__item analysis__item--tip">
                  {tip}
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Spell breakdown toggle */}
        {fight && Object.keys(fight.players).length > 0 && (
          <>
            <button
              className="analysis__btn analysis__btn--spells"
              onClick={() => setShowSpells(!showSpells)}
            >
              {showSpells ? "Spells ausblenden" : "Spell-Details anzeigen"}
            </button>
            {showSpells && <SpellBreakdown players={fight.players} />}
          </>
        )}
      </div>
    </div>
  );
}
