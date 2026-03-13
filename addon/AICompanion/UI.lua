AICompanion = AICompanion or {}
AICompanion.UI = AICompanion.UI or {}

local tipsFrame = nil
local currentCharacterKey = nil

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

local function sortedCharacterKeys()
  local keys = {}
  for key in pairs(AICompanionSV and AICompanionSV.characters or {}) do
    table.insert(keys, key)
  end
  table.sort(keys, function(a, b)
    local ia = AICompanionSV.characters[a] or {}
    local ib = AICompanionSV.characters[b] or {}
    return (ia.lastSeen or 0) > (ib.lastSeen or 0)
  end)
  return keys
end

local function findCharacterIndex(keys, key)
  for i, candidate in ipairs(keys) do
    if candidate == key then
      return i
    end
  end
  return nil
end

local function setSelectedCharacter(key)
  if key and AICompanionSV and AICompanionSV.characters and AICompanionSV.characters[key] then
    AICompanionCharSV.selectedCharacter = key
    currentCharacterKey = key
    return key
  end
  return nil
end

local function cycleCharacter(delta)
  local keys = sortedCharacterKeys()
  if #keys == 0 then
    return nil
  end
  local index = findCharacterIndex(keys, currentCharacterKey) or 1
  local nextIndex = index + delta
  if nextIndex < 1 then
    nextIndex = #keys
  elseif nextIndex > #keys then
    nextIndex = 1
  end
  return setSelectedCharacter(keys[nextIndex])
end

local function refreshTipsFrame(key)
  if not tipsFrame then
    return
  end
  local L = AICompanion.L or {}
  local tips, resolvedKey = getRecommendations(key)
  local lines = {}
  if resolvedKey then
    table.insert(lines, tostring(resolvedKey))
    table.insert(lines, "")
  end
  for i, tip in ipairs(tips or {}) do
    table.insert(lines, string.format("%d. %s", i, tostring(tip)))
  end
  if #lines == 0 then
    table.insert(lines, L.RECO_EMPTY or "No tips available for this character.")
  end

  tipsFrame.title:SetText(L.RECO_TITLE or "AI Companion - Tips")
  tipsFrame.text:SetText(table.concat(lines, "\n"))
  tipsFrame.charLabel:SetText("Char: " .. tostring(resolvedKey or "-"))
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
  text:SetPoint("BOTTOM", 0, 42)
  text:SetJustifyH("LEFT")
  text:SetJustifyV("TOP")
  text:SetSpacing(3)
  tipsFrame.text = text

  local charLabel = tipsFrame:CreateFontString(nil, "OVERLAY", "GameFontNormalSmall")
  charLabel:SetPoint("BOTTOMLEFT", 12, 14)
  charLabel:SetJustifyH("LEFT")
  tipsFrame.charLabel = charLabel

  local prev = CreateFrame("Button", nil, tipsFrame)
  prev:SetSize(90, 22)
  prev:SetPoint("BOTTOMRIGHT", -108, 10)
  local prevBg = prev:CreateTexture(nil, "BACKGROUND")
  prevBg:SetAllPoints(prev)
  prevBg:SetColorTexture(0.2, 0.2, 0.25, 0.9)
  local prevTxt = prev:CreateFontString(nil, "OVERLAY", "GameFontNormalSmall")
  prevTxt:SetPoint("CENTER")
  prevTxt:SetText("< Prev")
  prev:SetScript("OnClick", function()
    local nextKey = cycleCharacter(-1)
    if nextKey then
      refreshTipsFrame(nextKey)
    end
  end)

  local next = CreateFrame("Button", nil, tipsFrame)
  next:SetSize(90, 22)
  next:SetPoint("BOTTOMRIGHT", -12, 10)
  local nextBg = next:CreateTexture(nil, "BACKGROUND")
  nextBg:SetAllPoints(next)
  nextBg:SetColorTexture(0.2, 0.2, 0.25, 0.9)
  local nextTxt = next:CreateFontString(nil, "OVERLAY", "GameFontNormalSmall")
  nextTxt:SetPoint("CENTER")
  nextTxt:SetText("Next >")
  next:SetScript("OnClick", function()
    local nextKey = cycleCharacter(1)
    if nextKey then
      refreshTipsFrame(nextKey)
    end
  end)
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
  local resolvedInput = characterKey or AICompanion.ResolveCharacterKey("")
  local tips, resolvedKey = getRecommendations(resolvedInput)

  if not tips or #tips == 0 then
    print("|cff66ccffAICompanion:|r " .. (L.RECO_EMPTY or "No tips available for this character."))
    return
  end

  if isUiEnabled() then
    AICompanion.UI.Init()
    setSelectedCharacter(resolvedKey)
    refreshTipsFrame(resolvedKey)
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
