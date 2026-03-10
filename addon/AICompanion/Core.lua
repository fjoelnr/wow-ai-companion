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

local f = CreateFrame("Frame")
f:RegisterEvent("ADDON_LOADED")
f:RegisterEvent("PLAYER_LOGIN")
f:SetScript("OnEvent", function(_, event, arg1)
  if event == "ADDON_LOADED" and arg1 == "AICompanion" then
    loadLocale()
    AICompanionSV.sessions = AICompanionSV.sessions or {}
    AICompanionSV.characters = AICompanionSV.characters or {}
    AICompanionSV.recommendations = AICompanionSV.recommendations or {}
    AICompanionCharSV.pendingReco = AICompanionCharSV.pendingReco or {}
    AICompanionCharSV.selectedCharacter = AICompanionCharSV.selectedCharacter or nil
    AICompanionCharSV.characterKey = AICompanionCharSV.characterKey or nil
    SLASH_AICOMP1 = "/aicoach"
    SlashCmdList["AICOMP"] = function(msg)
      local command, rest = msg:match("^(%S+)%s*(.-)$")
      command = command or ""
      rest = rest or ""

      if command == "export" then
        AICompanion.ExportSession()
        print("|cff66ccffAICompanion:|r Export abgeschlossen. /reload ausführen, nachdem die Analyse lief.")
      elseif command == "tips" then
        AICompanion.UI.ShowReco(AICompanion.ResolveCharacterKey(rest))
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
        print("|cff66ccffAICompanion:|r /aicoach export | /aicoach tips [char] | /aicoach chars | /aicoach select <char>")
      end
    end
  elseif event == "PLAYER_LOGIN" then
    if AICompanion.Data and AICompanion.Data.BuildCharacterKey then
      AICompanionCharSV.characterKey = AICompanion.Data.BuildCharacterKey()
    end
    AICompanion.UI.Init()
    AICompanion.UI.MaybeShowRecoOnLogin()
  end
end)

function AICompanion.ResolveCharacterKey(query)
  if not query or query == "" then
    if AICompanionCharSV.selectedCharacter then
      return AICompanionCharSV.selectedCharacter
    end
    return AICompanionCharSV.characterKey
  end

  local normalized = query:lower():gsub("%s+", "")
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
  local count = 0
  for key, info in pairs(AICompanionSV.characters or {}) do
    count = count + 1
    print(
      "|cff66ccffAICompanion:|r",
      string.format(
        "%s | %s | Lvl %s | iLvl %s | %s",
        key,
        info.class or "?",
        info.level or "?",
        info.ilvl and string.format("%.1f", info.ilvl) or "?",
        info.zone or "?"
      )
    )
  end

  if count == 0 then
    print("|cff66ccffAICompanion:|r Noch keine exportierten Charaktere bekannt.")
  end
end

function AICompanion.ExportSession()
  local s = AICompanion.Data and AICompanion.Data.BuildSnapshot and AICompanion.Data.BuildSnapshot() or {}
  if not s.characterKey and AICompanion.Data and AICompanion.Data.BuildCharacterKey then
    s.characterKey = AICompanion.Data.BuildCharacterKey()
  end
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
    }
  end
end

-- Export-Hinweise bei Ereignissen
local e = CreateFrame("Frame")
e:RegisterEvent("ZONE_CHANGED_NEW_AREA")
e:RegisterEvent("QUEST_TURNED_IN")
e:RegisterEvent("PLAYER_ENTERING_WORLD")
e:SetScript("OnEvent", function(_, evt)
  local L = AICompanion.L or {}
  print("|cff66ccffAICompanion:|r", (L.HINT_EXPORT or "Export möglich:"), evt, "- /aicoach export oder Button.")
  if AICompanion and AICompanion.UI and AICompanion.UI.ShowExportPrompt then
    AICompanion.UI.ShowExportPrompt(evt)
  end
end)
