import { useCallback } from "react";
import { useWebSocket } from "../hooks/useWebSocket";
import { useCombatState } from "../hooks/useCombatState";
import { StatusBar } from "./StatusBar";
import { DPSMeter } from "./DPSMeter";
import { CombatFeed } from "./CombatFeed";
import { FightHistory } from "./FightHistory";
import { PlayerCard } from "./PlayerCard";
import { FightAnalysis } from "./FightAnalysis";
import type { FightSummary } from "../utils/types";

export function Dashboard() {
  const {
    state,
    handleMessage,
    dismissFight,
    setAnalysis,
    setAnalysisLoading,
  } = useCombatState();
  const { status } = useWebSocket({
    path: "/ws/dashboard",
    onMessage: handleMessage,
  });

  const handleAnalyzeFight = useCallback(
    async (fight: FightSummary) => {
      setAnalysisLoading(true);
      try {
        const resp = await fetch("/api/analyze-fight", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            fight,
            playerClass: state.session?.class ?? "",
            locale: state.session?.locale ?? "deDE",
          }),
        });
        if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
        const data = await resp.json();
        // Attach the fight to the analysis for display
        data.fight = fight;
        setAnalysis(data);
      } catch (err) {
        console.error("Fight analysis failed:", err);
        setAnalysis({
          summary: `Analyse fehlgeschlagen: ${err}`,
          rating: "?",
          highlights: [],
          improvements: [],
          tips: [],
          fight,
        });
      }
    },
    [state.session, setAnalysis, setAnalysisLoading],
  );

  const handleAnalyzeFromHistory = useCallback(
    (fight: FightSummary) => {
      handleAnalyzeFight(fight);
    },
    [handleAnalyzeFight],
  );

  return (
    <div className="dashboard">
      <StatusBar
        connection={status}
        session={state.session}
        inCombat={state.inCombat}
      />

      <main className="dashboard__grid">
        <div className="dashboard__col dashboard__col--left">
          <DPSMeter
            fight={state.activeFight}
            recentFights={state.fightHistory}
            mode="dps"
          />
          <DPSMeter
            fight={state.activeFight}
            recentFights={state.fightHistory}
            mode="hps"
          />
          <PlayerCard session={state.session} />
        </div>

        <div className="dashboard__col dashboard__col--right">
          <FightAnalysis
            analysis={state.latestAnalysis}
            loading={state.analysisLoading}
            activeFight={state.activeFight}
            onAnalyze={handleAnalyzeFight}
            onDismiss={dismissFight}
          />
          <CombatFeed events={state.combatEvents} />
          <FightHistory
            fights={state.fightHistory}
            onAnalyze={handleAnalyzeFromHistory}
          />
        </div>
      </main>
    </div>
  );
}
