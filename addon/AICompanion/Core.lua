AICompanion = AICompanion or {}
AICompanionSV = AICompanionSV or {}
AICompanionCharSV = AICompanionCharSV or {}

-- Minimaler Locale-Loader (fallback enUS)
local function loadLocale()
  local locale = GetLocale()
  local ok, L = pcall(function() return AICompanionLocale end)
  if ok and type(L)=="table" then AICompanion.L=L return end
  -- simple include order (TOC loads files, here just rely on globals)
  AICompanion.L = AICompanion.L or {}
end

local f = CreateFrame("Frame")
f:RegisterEvent("ADDON_LOADED")
f:RegisterEvent("PLAYER_LOGIN")
f:SetScript("OnEvent", function(_, event, arg1)
  if event == "ADDON_LOADED" and arg1 == "AICompanion" then
    loadLocale()
    AICompanionSV.sessions = AICompanionSV.sessions or {}
    AICompanionCharSV.pendingReco = AICompanionCharSV.pendingReco or {}
    SLASH_AICOMP1 = "/aicoach"
    SlashCmdList["AICOMP"] = function(msg)
      if msg == "export" then
        AICompanion.ExportSession()
        print("|cff66ccffAICompanion:|r Export abgeschlossen. /reload ausführen, nachdem die Analyse lief.")
      elseif msg == "tips" then
        AICompanion.UI.ShowReco()
      else
        print("|cff66ccffAICompanion:|r /aicoach export | /aicoach tips")
      end
    end
  elseif event == "PLAYER_LOGIN" then
    AICompanion.UI.Init()
    AICompanion.UI.MaybeShowRecoOnLogin()
  end
end)

function AICompanion.ExportSession()
  local spec = GetSpecialization() or 1
  local specId = select(1, GetSpecializationInfo(spec)) or 0
  local s = {
    ts = time(),
    player = UnitName("player"),
    class = select(2, UnitClass("player")),
    specId = specId,
    zone = GetZoneText(),
    fights = AICompanion.Combat and AICompanion.Combat.Flush() or {},
    locale = GetLocale(),
  }
  table.insert(AICompanionSV.sessions, s)
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
