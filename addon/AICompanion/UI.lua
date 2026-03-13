AICompanion = AICompanion or {}
AICompanion.UI = AICompanion.UI or {}

local tipsFrame = nil

local function getRecommendations(characterKey)
  local key = characterKey or AICompanionCharSV.selectedCharacter or AICompanionCharSV.characterKey
  local accountReco = AICompanionSV and AICompanionSV.recommendations and key and AICompanionSV.recommendations[key]
  if accountReco and type(accountReco.tips) == "table" then
    return accountReco.tips, key
  end
  return AICompanionCharSV.pendingReco or {}, key
end

local function isUiEnabled()
  local settings = AICompanionSV and AICompanionSV.settings
  return settings and settings.uiEnabled == true
end

function AICompanion.UI.Init()
  if tipsFrame then
    return
  end

  tipsFrame = CreateFrame("Frame", nil, UIParent)
  tipsFrame:SetSize(480, 320)
  tipsFrame:SetPoint("CENTER")
  tipsFrame:Hide()
  tipsFrame:SetFrameStrata("DIALOG")

  local bg = tipsFrame:CreateTexture(nil, "BACKGROUND")
  bg:SetAllPoints(tipsFrame)
  bg:SetColorTexture(0.05, 0.05, 0.08, 0.95)

  local title = tipsFrame:CreateFontString(nil, "OVERLAY", "GameFontNormal")
  title:SetPoint("TOPLEFT", 12, -10)
  title:SetPoint("TOPRIGHT", -12, -10)
  title:SetJustifyH("LEFT")
  tipsFrame.title = title

  local text = tipsFrame:CreateFontString(nil, "OVERLAY", "GameFontHighlightSmall")
  text:SetPoint("TOPLEFT", 12, -36)
  text:SetPoint("TOPRIGHT", -12, -36)
  text:SetPoint("BOTTOM", 0, 12)
  text:SetJustifyH("LEFT")
  text:SetJustifyV("TOP")
  text:SetSpacing(3)
  tipsFrame.text = text
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

  if not tips or #tips == 0 then
    print("|cff66ccffAICompanion:|r " .. (L.RECO_EMPTY or "No tips available for this character."))
    return
  end

  if isUiEnabled() then
    AICompanion.UI.Init()
    local lines = {}
    if resolvedKey then
      table.insert(lines, tostring(resolvedKey))
      table.insert(lines, "")
    end
    for i, tip in ipairs(tips) do
      table.insert(lines, string.format("%d. %s", i, tostring(tip)))
    end
    tipsFrame.title:SetText(L.RECO_TITLE or "AI Companion - Tips")
    tipsFrame.text:SetText(table.concat(lines, "\n"))
    tipsFrame:Show()
    return
  end

  print("|cff66ccffAICompanion:|r " .. (L.RECO_TITLE or "AI Companion - Tips"))
  if resolvedKey then
    print("|cff66ccffAICompanion:|r Character: " .. tostring(resolvedKey))
  end
  for i, tip in ipairs(tips) do
    print(string.format("|cff00ff88%d.|r %s", i, tostring(tip)))
  end
end
