import type { ConnectionStatus, SessionData } from "../utils/types";
import { getClassColor } from "../utils/classColors";

interface StatusBarProps {
  connection: ConnectionStatus;
  session: SessionData | null;
  inCombat: boolean;
}

const STATUS_COLORS: Record<ConnectionStatus, string> = {
  connected: "#00ff88",
  connecting: "#ffaa00",
  disconnected: "#ff4444",
};

const STATUS_LABELS: Record<ConnectionStatus, string> = {
  connected: "Connected",
  connecting: "Connecting...",
  disconnected: "Disconnected",
};

export function StatusBar({ connection, session, inCombat }: StatusBarProps) {
  const classColor = session?.class ? getClassColor(session.class) : "#999";

  return (
    <header className="status-bar">
      <div className="status-bar__left">
        <span className="status-bar__title">⚔️ WoW AI Companion</span>
        <span
          className="status-bar__indicator"
          style={{ color: STATUS_COLORS[connection] }}
        >
          ● {STATUS_LABELS[connection]}
        </span>
      </div>

      <div className="status-bar__center">
        {inCombat ? (
          <span className="status-bar__combat status-bar__combat--active">
            ⚔ IN COMBAT
          </span>
        ) : (
          <span className="status-bar__combat">Out of Combat</span>
        )}
      </div>

      <div className="status-bar__right">
        {session?.player ? (
          <span style={{ color: classColor }}>
            {session.player}
            {session.ilvl ? ` (${Math.round(session.ilvl)} iLvl)` : ""}
            {session.zone ? ` – ${session.zone}` : ""}
          </span>
        ) : (
          <span style={{ color: "#666" }}>No character data</span>
        )}
      </div>
    </header>
  );
}
