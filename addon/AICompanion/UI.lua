AICompanion = AICompanion or {}
AICompanion.UI = AICompanion.UI or {}

local panel, recoFrame

local function getRecommendations(characterKey)
  local key = characterKey or AICompanionCharSV.selectedCharacter or AICompanionCharSV.characterKey
  local accountReco = AICompanionSV and AICompanionSV.recommendations and key and AICompanionSV.recommendations[key]
  if accountReco and type(accountReco.tips) == "table" then
    return accountReco.tips, key, accountReco.updatedAt
  end
  return AICompanionCharSV.pendingReco or {}, key, nil
end

local function makeMovable(frame)
  frame:SetMovable(true)
  frame:EnableMouse(true)
  frame:RegisterForDrag("LeftButton")
  frame:SetClampedToScreen(true)
  frame:SetScript("OnDragStart", function(self)
    self:StartMoving()
  end)
  frame:SetScript("OnDragStop", function(self)
    self:StopMovingOrSizing()
  end)
end

local function styleFrame(frame)
  local bg = frame:CreateTexture(nil, "BACKGROUND")
  bg:SetAllPoints(frame)
  bg:SetColorTexture(0.05, 0.05, 0.08, 0.96)
  frame.bg = bg

  local border = CreateFrame("Frame", nil, frame)
  border:SetAllPoints(frame)
  border:SetBackdrop({
    edgeFile = "Interface\\Tooltips\\UI-Tooltip-Border",
    edgeSize = 14,
  })
  border:SetBackdropBorderColor(0.4, 0.4, 0.45, 1)
  border:EnableMouse(false)
  frame.border = border
end

local function createTitle(frame, text)
  local title = frame:CreateFontString(nil, "OVERLAY", "GameFontNormal")
  title:SetPoint("TOPLEFT", 14, -12)
  title:SetPoint("TOPRIGHT", -40, -12)
  title:SetJustifyH("LEFT")
  title:SetText(text)
  return title
end

local function createCloseButton(parent)
  local close = CreateFrame("Button", nil, parent)
  close:SetSize(24, 24)
  close:SetPoint("TOPRIGHT", -8, -8)
  local bg = close:CreateTexture(nil, "BACKGROUND")
  bg:SetAllPoints(close)
  bg:SetColorTexture(0.45, 0.12, 0.12, 0.95)
  local label = close:CreateFontString(nil, "OVERLAY", "GameFontNormal")
  label:SetPoint("CENTER")
  label:SetText("X")
  close:SetScript("OnEnter", function()
    bg:SetColorTexture(0.6, 0.16, 0.16, 1)
  end)
  close:SetScript("OnLeave", function()
    bg:SetColorTexture(0.45, 0.12, 0.12, 0.95)
  end)
  return close
end

local function createActionButton(parent, width, height, label, onClick)
  local btn = CreateFrame("Button", nil, parent)
  btn:SetSize(width, height)
  local bg = btn:CreateTexture(nil, "BACKGROUND")
  bg:SetAllPoints(btn)
  bg:SetColorTexture(0.3, 0.08, 0.08, 0.95)
  local text = btn:CreateFontString(nil, "OVERLAY", "GameFontNormal")
  text:SetPoint("CENTER")
  text:SetText(label)
  btn.label = text
  btn:SetScript("OnClick", onClick)
  btn:SetScript("OnEnter", function()
    bg:SetColorTexture(0.45, 0.12, 0.12, 1)
  end)
  btn:SetScript("OnLeave", function()
    bg:SetColorTexture(0.3, 0.08, 0.08, 0.95)
  end)
  function btn:SetText(value)
    self.label:SetText(value)
  end
  return btn
end

local function createBodyText(parent, width)
  local text = parent:CreateFontString(nil, "OVERLAY", "GameFontHighlightSmall")
  text:SetJustifyH("LEFT")
  text:SetJustifyV("TOP")
  text:SetSpacing(3)
  text:SetWidth(width)
  return text
end

function AICompanion.UI.Init()
  if panel then
    return
  end

  panel = CreateFrame("Frame", nil, UIParent)
  panel:SetSize(420, 220)
  panel:SetPoint("CENTER", 0, 80)
  panel:Hide()
  panel:SetFrameStrata("DIALOG")
  styleFrame(panel)
  makeMovable(panel)

  panel.title = createTitle(panel, "AI Companion - Export")
  createCloseButton(panel):SetScript("OnClick", function()
    panel:Hide()
  end)

  local text = createBodyText(panel, 390)
  text:SetPoint("TOPLEFT", 16, -42)
  panel.text = text

  local exportBtn = createActionButton(panel, 200, 24, "Jetzt exportieren", function()
    if AICompanion.ExportSession then
      AICompanion.ExportSession("manual")
      print("|cff66ccffAICompanion:|r Snapshot geschrieben. Fuer externe Synchronisierung bitte /reload ausfuehren.")
    end
  end)
  exportBtn:SetPoint("BOTTOM", 0, 38)
  panel.exportBtn = exportBtn

  local closeBtn = createActionButton(panel, 120, 24, "Spaeter", function()
    panel:Hide()
  end)
  closeBtn:SetPoint("BOTTOM", 0, 10)
  panel.closeBtn = closeBtn
end

function AICompanion.UI.ShowExportPrompt(reason)
  AICompanion.UI.Init()
  local L = AICompanion.L or {}
  local title = L.EXPORT_TITLE or "AI Companion - Export"
  local msgT = L.EXPORT_MSG or "Daten exportieren (%s)? Fuer externe Synchronisierung danach /reload ausfuehren."
  local btnT = L.EXPORT_NOW or "Jetzt exportieren"
  local laterT = L.LATER or "Spaeter"
  panel.title:SetText(title)
  panel.text:SetText(string.format(msgT, reason or (L.MANUAL or "manuell")))
  panel.exportBtn:SetText(btnT)
  panel.closeBtn:SetText(laterT)
  panel:Show()
end

local function buildReco()
  if recoFrame then
    return
  end

  recoFrame = CreateFrame("Frame", nil, UIParent)
  recoFrame:SetSize(460, 340)
  recoFrame:SetPoint("CENTER")
  recoFrame:Hide()
  recoFrame:SetFrameStrata("DIALOG")
  styleFrame(recoFrame)
  makeMovable(recoFrame)

  recoFrame.title = createTitle(recoFrame, "AI Companion - Tipps")
  createCloseButton(recoFrame)

  local text = createBodyText(recoFrame, 420)
  text:SetPoint("TOPLEFT", 18, -42)
  recoFrame.text = text

  local btn = createActionButton(recoFrame, 160, 24, "Schliessen", function()
    recoFrame:Hide()
  end)
  btn:SetPoint("BOTTOM", 0, 12)
  recoFrame.closeBtn = btn
end

function AICompanion.UI.MaybeShowRecoOnLogin()
  local tips = getRecommendations()
  if tips and #tips > 0 then
    AICompanion.UI.ShowReco()
  end
end

function AICompanion.UI.ShowReco(characterKey)
  buildReco()
  local L = AICompanion.L or {}
  recoFrame.title:SetText(L.RECO_TITLE or "AI Companion - Tipps")
  local tips, resolvedKey = getRecommendations(characterKey)
  local lines = {}

  if resolvedKey then
    table.insert(lines, ("|cff66ccff%s|r"):format(resolvedKey))
    table.insert(lines, "")
  end

  for _, r in ipairs(tips or {}) do
    table.insert(lines, ("|cff00ff88-|r %s"):format(r))
  end

  if #lines == 0 then
    table.insert(lines, L.RECO_EMPTY or "Keine Tipps fuer diesen Charakter vorhanden.")
  end

  recoFrame.text:SetText(table.concat(lines, "\n"))
  recoFrame:Show()
end
