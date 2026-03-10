import { useEffect, useState } from "react";

type CharacterSummary = {
  characterKey: string;
  player?: string;
  realm?: string;
  class?: string;
  level?: number;
  ilvl?: number;
  zone?: string;
  ts?: number;
};

type SessionData = {
  characterKey?: string;
  player?: string;
  realm?: string;
  class?: string;
  level?: number;
  ilvl?: number;
  zone?: string;
  location?: {
    mapName?: string | null;
    subZone?: string | null;
    realZone?: string | null;
  };
  activeQuests?: Array<{ id?: number; title?: string; isComplete?: boolean }>;
  professions?: Array<{ name?: string; skillLevel?: number; maxLevel?: number }>;
  gold?: number;
};

type RecommendationData = {
  characterKey?: string;
  tips?: string[];
  updatedAt?: number;
};

function formatGold(copper?: number) {
  if (!copper) return "0g";
  const gold = Math.floor(copper / 10000);
  const silver = Math.floor((copper % 10000) / 100);
  return `${gold}g ${silver}s`;
}

async function fetchJson<T>(url: string): Promise<T> {
  const resp = await fetch(url);
  if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
  return resp.json() as Promise<T>;
}

export default function App() {
  const [characters, setCharacters] = useState<CharacterSummary[]>([]);
  const [selectedCharacter, setSelectedCharacter] = useState<string>("");
  const [session, setSession] = useState<SessionData | null>(null);
  const [recommendations, setRecommendations] = useState<RecommendationData | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;

    async function loadCharacters() {
      try {
        const list = await fetchJson<CharacterSummary[]>("/api/characters");
        if (cancelled) return;
        setCharacters(list);
        setSelectedCharacter((current) => current || list[0]?.characterKey || "");
        setError("");
      } catch (err) {
        if (!cancelled) setError(String(err));
      }
    }

    loadCharacters();
    const timer = window.setInterval(loadCharacters, 10000);
    return () => {
      cancelled = true;
      window.clearInterval(timer);
    };
  }, []);

  useEffect(() => {
    if (!selectedCharacter) {
      setSession(null);
      setRecommendations(null);
      return;
    }

    let cancelled = false;

    async function loadCharacterData() {
      try {
        const [sessionData, recommendationData] = await Promise.all([
          fetchJson<SessionData>(`/api/session?character_key=${encodeURIComponent(selectedCharacter)}`),
          fetchJson<RecommendationData>(`/api/recommendations?character_key=${encodeURIComponent(selectedCharacter)}`),
        ]);
        if (cancelled) return;
        setSession(sessionData);
        setRecommendations(recommendationData);
        setError("");
      } catch (err) {
        if (!cancelled) setError(String(err));
      }
    }

    loadCharacterData();
    const timer = window.setInterval(loadCharacterData, 8000);
    return () => {
      cancelled = true;
      window.clearInterval(timer);
    };
  }, [selectedCharacter]);

  return (
    <div className="qa-app">
      <header className="qa-header">
        <div>
          <p className="qa-eyebrow">WoW AI Companion</p>
          <h1>Quest and Character Assistant</h1>
        </div>
        <div className="qa-header__status">
          <span className="qa-dot" />
          <span>{error ? "Degraded" : "Connected"}</span>
        </div>
      </header>

      <main className="qa-layout">
        <section className="qa-panel qa-panel--sidebar">
          <div className="qa-panel__head">
            <h2>Characters</h2>
            <span>{characters.length}</span>
          </div>
          <div className="qa-characters">
            {characters.map((character) => (
              <button
                key={character.characterKey}
                className={`qa-character ${selectedCharacter === character.characterKey ? "is-active" : ""}`}
                onClick={() => setSelectedCharacter(character.characterKey)}
                type="button"
              >
                <strong>{character.player}</strong>
                <span>{character.realm}</span>
                <span>{character.class} · Lvl {character.level ?? "?"}</span>
                <span>{character.zone || "Unknown zone"}</span>
              </button>
            ))}
            {characters.length === 0 && <p className="qa-empty">No exported characters yet.</p>}
          </div>
        </section>

        <section className="qa-main">
          <section className="qa-panel">
            <div className="qa-panel__head">
              <h2>Overview</h2>
              <span>{session?.characterKey || "No selection"}</span>
            </div>
            {session ? (
              <div className="qa-grid">
                <div className="qa-stat">
                  <label>Class</label>
                  <strong>{session.class || "?"}</strong>
                </div>
                <div className="qa-stat">
                  <label>Level</label>
                  <strong>{session.level ?? "?"}</strong>
                </div>
                <div className="qa-stat">
                  <label>Itemlevel</label>
                  <strong>{session.ilvl ?? "?"}</strong>
                </div>
                <div className="qa-stat">
                  <label>Gold</label>
                  <strong>{formatGold(session.gold)}</strong>
                </div>
                <div className="qa-stat qa-stat--wide">
                  <label>Location</label>
                  <strong>
                    {session.zone || "Unknown zone"}
                    {session.location?.subZone ? ` · ${session.location.subZone}` : ""}
                  </strong>
                </div>
              </div>
            ) : (
              <p className="qa-empty">Select a character or export one in-game first.</p>
            )}
          </section>

          <section className="qa-two-up">
            <section className="qa-panel">
              <div className="qa-panel__head">
                <h2>Quest Focus</h2>
                <span>{session?.activeQuests?.length || 0}</span>
              </div>
              <div className="qa-list">
                {(session?.activeQuests || []).slice(0, 12).map((quest) => (
                  <article className="qa-list__item" key={`${quest.id}-${quest.title}`}>
                    <strong>{quest.title || `Quest ${quest.id}`}</strong>
                    <span>{quest.isComplete ? "Ready to turn in" : "In progress"}</span>
                  </article>
                ))}
                {(!session?.activeQuests || session.activeQuests.length === 0) && (
                  <p className="qa-empty">No quest data exported yet.</p>
                )}
              </div>
            </section>

            <section className="qa-panel">
              <div className="qa-panel__head">
                <h2>Professions</h2>
                <span>{session?.professions?.length || 0}</span>
              </div>
              <div className="qa-list">
                {(session?.professions || []).map((profession) => (
                  <article className="qa-list__item" key={profession.name}>
                    <strong>{profession.name || "Unknown profession"}</strong>
                    <span>
                      {profession.skillLevel ?? 0} / {profession.maxLevel ?? 0}
                    </span>
                  </article>
                ))}
                {(!session?.professions || session.professions.length === 0) && (
                  <p className="qa-empty">No profession data exported yet.</p>
                )}
              </div>
            </section>
          </section>

          <section className="qa-panel">
            <div className="qa-panel__head">
              <h2>Recommendations</h2>
              <span>{recommendations?.tips?.length || 0}</span>
            </div>
            <div className="qa-list">
              {(recommendations?.tips || []).map((tip, index) => (
                <article className="qa-list__item" key={`${index}-${tip}`}>
                  <strong>Tip {index + 1}</strong>
                  <span>{tip}</span>
                </article>
              ))}
              {(!recommendations?.tips || recommendations.tips.length === 0) && (
                <p className="qa-empty">No recommendations stored for this character yet.</p>
              )}
            </div>
          </section>
        </section>
      </main>
    </div>
  );
}
