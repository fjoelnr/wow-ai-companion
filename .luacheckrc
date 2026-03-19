std = "lua51"

-- WoW APIs & eigene Addon-Globals erlauben
globals = {
  -- Addon
  "AICompanion", "AICompanionSV", "AICompanionCharSV",

  -- WoW UI & Frames
  "CreateFrame", "UIParent",

  -- Chat/Print/Slash
  "print", "SlashCmdList", "SLASH_AICOMP1",

  -- Zeit & util
  "time", "select",

  -- Spiel-API (oft genutzt)
  "GetLocale", "UnitName", "UnitClass",
  "GetSpecialization", "GetSpecializationInfo",
  "GetZoneText", "GetInstanceInfo",
  "CombatLogGetCurrentEventInfo", "UnitGUID",
  "ReloadUI",

  -- Fonts/Templates (Strings tauchen nicht auf, aber schadet nicht)
  "GameFontHighlight", "GameFontHighlightSmall",
}

-- Häufig harmlose Warnungen reduzieren
-- 111: setting global; 113: accessing undefined variable
-- 121/122: mutating non-standard globals/upvalues
ignore = {
  "111", "113", "121", "122",
  -- optional: ungenutzte var _ / Funktionsargs
  "211/_", "212/_", "213/_", "214/_", "215/_",
}
