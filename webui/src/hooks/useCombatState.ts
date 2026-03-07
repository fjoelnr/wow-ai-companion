import { useCallback, useState } from "react";
import type {
  CombatEvent,
  DashboardState,
  FightAnalysis,
  FightSummary,
  SessionData,
  WSMessage,
} from "../utils/types";

const MAX_EVENTS = 200;
const MAX_HISTORY = 50;

const INITIAL_STATE: DashboardState = {
  connection: "connecting",
  session: null,
  combatEvents: [],
  fightHistory: [],
  activeFight: null,
  latestAnalysis: null,
  analysisLoading: false,
  inCombat: false,
};

/**
 * Central state management for the dashboard.
 * Processes incoming WebSocket messages and maintains all UI state.
 */
export function useCombatState() {
  const [state, setState] = useState<DashboardState>(INITIAL_STATE);

  const handleMessage = useCallback((msg: WSMessage) => {
    setState((prev) => {
      switch (msg.type) {
        case "init":
          return {
            ...prev,
            session: msg.data.session ?? null,
            fightHistory: msg.data.recentFights ?? [],
          };

        case "combat_event": {
          const event = msg.data as CombatEvent;
          // If we weren't in combat, clear old events for a fresh start
          const baseEvents = prev.inCombat ? prev.combatEvents : [];
          const events = [...baseEvents, event];
          // Keep buffer bounded
          const trimmed = events.length > MAX_EVENTS
            ? events.slice(events.length - MAX_EVENTS)
            : events;

          return {
            ...prev,
            combatEvents: trimmed,
            inCombat: true,
          };
        }

        case "fight_end": {
          const fight = msg.data as FightSummary;
          const history = [...prev.fightHistory, fight];
          const trimmedHistory = history.length > MAX_HISTORY
            ? history.slice(history.length - MAX_HISTORY)
            : history;

          return {
            ...prev,
            fightHistory: trimmedHistory,
            activeFight: fight,
            inCombat: false,
            // Keep combatEvents visible for review; cleared on next combat start
          };
        }

        case "fight_analysis":
          return {
            ...prev,
            latestAnalysis: msg.data as FightAnalysis,
            analysisLoading: false,
          };

        case "session_update":
          return {
            ...prev,
            session: msg.data as SessionData,
          };

        default:
          return prev;
      }
    });
  }, []);

  const setConnection = useCallback(
    (status: DashboardState["connection"]) => {
      setState((prev) => ({ ...prev, connection: status }));
    },
    [],
  );

  const dismissFight = useCallback(() => {
    setState((prev) => ({ ...prev, activeFight: null }));
  }, []);

  const setAnalysis = useCallback((analysis: FightAnalysis | null) => {
    setState((prev) => ({ ...prev, latestAnalysis: analysis, analysisLoading: false }));
  }, []);

  const setAnalysisLoading = useCallback((loading: boolean) => {
    setState((prev) => ({ ...prev, analysisLoading: loading }));
  }, []);

  return {
    state,
    handleMessage,
    setConnection,
    dismissFight,
    setAnalysis,
    setAnalysisLoading,
  };
}
