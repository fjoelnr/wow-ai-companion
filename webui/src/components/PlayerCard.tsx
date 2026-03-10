import type { SessionData } from "../utils/types";
import { getClassColor, CLASS_ICONS } from "../utils/classColors";

interface PlayerCardProps {
  session: SessionData | null;
}

export function PlayerCard({ session }: PlayerCardProps) {
  if (!session?.player) {
    return (
      <div className="panel player-card">
        <h3>Character</h3>
        <p className="panel__empty">No character data. Export in-game with /aicoach export</p>
      </div>
    );
  }

  const classColor = session.class ? getClassColor(session.class) : "#999";
  const classIcon = session.class ? CLASS_ICONS[session.class.toUpperCase()] ?? "" : "";

  return (
    <div className="panel player-card">
      <h3>Character</h3>
      <div className="player-card__info">
        <div className="player-card__name" style={{ color: classColor }}>
          {classIcon} {session.player}
        </div>
        <div className="player-card__details">
          {session.class && <span>Class: {session.class}</span>}
          {session.level && <span>Level: {session.level}</span>}
          {session.ilvl && <span>iLvl: {Math.round(session.ilvl)}</span>}
        </div>
        {session.location && (
          <div className="player-card__location">
            📍 {session.location.zone}
            {session.location.subZone && ` – ${session.location.subZone}`}
          </div>
        )}
        {session.professions && session.professions.length > 0 && (
          <div className="player-card__professions">
            {session.professions.map((p, i) => (
              <span key={i}>
                {p.name}: {p.skillLevel}/{p.maxLevel}
              </span>
            ))}
          </div>
        )}
        {session.activeQuests && (
          <div className="player-card__quests">
            Active Quests: {session.activeQuests.length}
            {session.activeQuests.filter((q) => q.isComplete).length > 0 && (
              <span className="player-card__ready">
                {" "}({session.activeQuests.filter((q) => q.isComplete).length} ready to turn in)
              </span>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
