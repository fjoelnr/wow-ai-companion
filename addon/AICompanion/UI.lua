AICompanion = AICompanion or {}
AICompanion.UI = AICompanion.UI or {}

local function getRecommendations(characterKey)
  local key = characterKey or AICompanionCharSV.selectedCharacter or AICompanionCharSV.characterKey
  local accountReco = AICompanionSV and AICompanionSV.recommendations and key and AICompanionSV.recommendations[key]
  if accountReco and type(accountReco.tips) == "table" then
    return accountReco.tips, key
  end
  return AICompanionCharSV.pendingReco or {}, key
end

function AICompanion.UI.Init()
  -- Intentionally no custom UI frames. This avoids taint/protected UI interactions.
end

function AICompanion.UI.ShowExportPrompt(reason)
  local L = AICompanion.L or {}
  print("|cff66ccffAICompanion:|r " .. (L.HINT_EXPORT or "Export now available") .. " (" .. tostring(reason or "manual") .. ")")
end

function AICompanion.UI.MaybeShowRecoOnLogin()
  -- No auto popup on login/reload.
end

function AICompanion.UI.ShowReco(characterKey)
  local L = AICompanion.L or {}
  local tips, resolvedKey = getRecommendations(characterKey)
  print("|cff66ccffAICompanion:|r " .. (L.RECO_TITLE or "AI Companion - Tips"))
  if resolvedKey then
    print("|cff66ccffAICompanion:|r Character: " .. tostring(resolvedKey))
  end

  if not tips or #tips == 0 then
    print("|cff66ccffAICompanion:|r " .. (L.RECO_EMPTY or "No tips available for this character."))
    return
  end

  for i, tip in ipairs(tips) do
    print(string.format("|cff00ff88%d.|r %s", i, tostring(tip)))
  end
end
