AICompanion = AICompanion or {}
AICompanionSV = AICompanionSV or {}
AICompanionCharSV = AICompanionCharSV or {}

-- Minimaler Locale-Loader (fallback enUS)
local function loadLocale()
  local ok, L = pcall(function() return AICompanionLocale end)
  if ok and type(L) == "table" then
    AICompanion.L = L
  else
    AICompanion.L = AICompanion.L or {}
  end
end

local function exportSnapshot(reason)
  local s = AICompanion.Data and AICompanion.Data.BuildSnapshot and AICompanion.Data.BuildSnapshot() or {}
  if not s.characterKey and AICompanion.Data and AICompanion.Data.BuildCharacterKey then
    s.characterKey = AICompanion.Data.BuildCharacterKey()
  end
  s.syncReason = reason or "manual"
  table.insert(AICompanionSV.sessions, s)

  if s.characterKey then
    AICompanionCharSV.characterKey = s.characterKey
    AICompanionSV.characters[s.characterKey] = {
      player = s.player,
      realm = s.realm,
      class = s.class,
      level = s.level,
      ilvl = s.ilvl,
      zone = s.zone,
      mapId = s.mapId,
      lastSeen = s.ts,
      lastSyncReason = s.syncReason,
    }
  end
end

local function sortedCharacterKeys()
  local keys = {}
  for key in pairs(AICompanionSV.characters or {}) do
    table.insert(keys, key)
  end
  table.sort(keys, function(a, b)
    local ia = AICompanionSV.characters[a] or {}
    local ib = AICompanionSV.characters[b] or {}
    return (ia.lastSeen or 0) > (ib.lastSeen or 0)
  end)
  return keys
end

local function getDefaultCharacterKey()
  if AICompanionCharSV.selectedCharacter and AICompanionSV.characters[AICompanionCharSV.selectedCharacter] then
    return AICompanionCharSV.selectedCharacter
  end
  if AICompanionCharSV.characterKey and AICompanionSV.characters[AICompanionCharSV.characterKey] then
    return AICompanionCharSV.characterKey
  end
  local keys = sortedCharacterKeys()
  return keys[1]
end

local f = CreateFrame("Frame")
f:RegisterEvent("ADDON_LOADED")
f:SetScript("OnEvent", function(_, event, arg1)
  if event == "ADDON_LOADED" and arg1 == "AICompanion" then
    loadLocale()
    AICompanionSV.sessions = AICompanionSV.sessions or {}
    AICompanionSV.characters = AICompanionSV.characters or {}
    AICompanionSV.recommendations = AICompanionSV.recommendations or {}
    AICompanionSV.settings = AICompanionSV.settings or {}
    if AICompanionSV.settings.uiEnabled == nil then
      AICompanionSV.settings.uiEnabled = false
    end
    AICompanionCharSV.pendingReco = AICompanionCharSV.pendingReco or {}
    AICompanionCharSV.selectedCharacter = AICompanionCharSV.selectedCharacter or nil
    AICompanionCharSV.characterKey = AICompanionCharSV.characterKey or nil
    SLASH_AICOMP1 = "/aicoach"
    SlashCmdList["AICOMP"] = function(msg)
      local command, rest = msg:match("^(%S+)%s*(.-)$")
      command = command or ""
      rest = rest or ""

      if command == "export" then
        AICompanion.ExportSession("manual")
        print("|cff66ccffAICompanion:|r Export abgeschlossen. Für externe Synchronisierung bitte /reload ausführen.")
      elseif command == "syncnow" then
        AICompanion.ExportSession("manual")
        print("|cff66ccffAICompanion:|r Snapshot geschrieben. Bitte /reload ausführen, damit WoW die Daten auf Disk speichert.")
      elseif command == "tips" then
        AICompanion.UI.ShowReco(AICompanion.ResolveCharacterKey(rest))
      elseif command == "ui" then
        local opt = (rest or ""):lower()
        if opt == "on" then
          AICompanionSV.settings.uiEnabled = true
          print("|cff66ccffAICompanion:|r UI-Fenster aktiviert.")
        elseif opt == "off" then
          AICompanionSV.settings.uiEnabled = false
          print("|cff66ccffAICompanion:|r UI-Fenster deaktiviert (Chat-only).")
        else
          local state = AICompanionSV.settings.uiEnabled and "on" or "off"
          print("|cff66ccffAICompanion:|r UI-Status:", state, "- nutze /aicoach ui on|off")
        end
      elseif command == "chars" then
        AICompanion.ListKnownCharacters()
      elseif command == "select" then
        local selected = AICompanion.ResolveCharacterKey(rest)
        if selected then
          AICompanionCharSV.selectedCharacter = selected
          print("|cff66ccffAICompanion:|r Ausgewählter Charakter:", selected)
        else
          print("|cff66ccffAICompanion:|r Kein Charakter gefunden für:", rest)
        end
      else
        print("|cff66ccffAICompanion:|r /aicoach export | /aicoach syncnow | /aicoach tips [char] | /aicoach ui on|off | /aicoach chars | /aicoach select <char>")
      end
    end
  end
end)

function AICompanion.ResolveCharacterKey(query)
  if not query or query == "" then
    return getDefaultCharacterKey()
  end

  local normalized = query:lower():gsub("%s+", "")
  local asNumber = tonumber(query)
  if asNumber then
    local keys = sortedCharacterKeys()
    return keys[asNumber]
  end

  local exact = AICompanionSV.characters[query]
  if exact then
    return query
  end

  for key, info in pairs(AICompanionSV.characters or {}) do
    local candidate = key:lower():gsub("%s+", "")
    local name = ((info and info.player) or ""):lower():gsub("%s+", "")
    if candidate == normalized or name == normalized then
      return key
    end
  end

  return nil
end

function AICompanion.ListKnownCharacters()
  local keys = sortedCharacterKeys()
  local selected = getDefaultCharacterKey()
  for i, key in ipairs(keys) do
    local info = AICompanionSV.characters[key] or {}
    local marker = (key == selected) and "*" or " "
    print(
      "|cff66ccffAICompanion:|r",
      string.format(
        "[%d]%s %s | %s | Lvl %s | iLvl %s | %s",
        i,
        marker,
        key,
        info.class or "?",
        info.level or "?",
        info.ilvl and string.format("%.1f", info.ilvl) or "?",
        info.zone or "?"
      )
    )
  end

  if #keys == 0 then
    print("|cff66ccffAICompanion:|r Noch keine exportierten Charaktere bekannt.")
  end
end

function AICompanion.ExportSession(reason)
  exportSnapshot(reason)
end
