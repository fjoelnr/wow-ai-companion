/** WoW class colors (official Blizzard hex values). */

export const CLASS_COLORS: Record<string, string> = {
  WARRIOR: "#C69B6D",
  PALADIN: "#F48CBA",
  HUNTER: "#AAD372",
  ROGUE: "#FFF468",
  PRIEST: "#FFFFFF",
  DEATHKNIGHT: "#C41E3A",
  SHAMAN: "#0070DD",
  MAGE: "#3FC7EB",
  WARLOCK: "#8788EE",
  MONK: "#00FF98",
  DRUID: "#FF7C0A",
  DEMONHUNTER: "#A330C9",
  EVOKER: "#33937F",
};

export function getClassColor(className: string): string {
  return CLASS_COLORS[className.toUpperCase()] ?? "#999999";
}

/** Class icons (emoji fallback – replace with actual icons later). */
export const CLASS_ICONS: Record<string, string> = {
  WARRIOR: "🗡️",
  PALADIN: "🛡️",
  HUNTER: "🏹",
  ROGUE: "🗡️",
  PRIEST: "✨",
  DEATHKNIGHT: "💀",
  SHAMAN: "⚡",
  MAGE: "❄️",
  WARLOCK: "🔮",
  MONK: "☯️",
  DRUID: "🐻",
  DEMONHUNTER: "👁️",
  EVOKER: "🐉",
};
