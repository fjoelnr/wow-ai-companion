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

-- Export-Prompt
function AICompanion.UI.Init()
  if panel then return end
  panel = CreateFrame("Frame", "AICompanionExportFrame", UIParent, "BasicFrameTemplateWithInset")
  panel:SetSize(420, 220)
  panel:SetPoint("CENTER")
  panel:Hide()

  panel.title = panel:CreateFontString(nil, "OVERLAY", "GameFontHighlight")
  panel.title:SetPoint("TOP", 0, -10)
  panel.title:SetText("AI Companion – Export")

  local text = panel:CreateFontString(nil, "OVERLAY", "GameFontHighlightSmall")
  text:SetPoint("TOPLEFT", 15, -40)
  text:SetJustifyH("LEFT")
  text:SetWidth(390)
  panel.text = text

  local btn = CreateFrame("Button", nil, panel, "GameMenuButtonTemplate")
  btn:SetPoint("BOTTOM", 0, 40)
  btn:SetSize(200, 24)
  btn:SetText("Jetzt exportieren")
  btn:SetScript("OnClick", function()
    if AICompanion.ExportSession then
      AICompanion.ExportSession()
    end
    ReloadUI()
  end)
  panel.exportBtn = btn

  local close = CreateFrame("Button", nil, panel, "GameMenuButtonTemplate")
  close:SetPoint("BOTTOM", 0, 10)
  close:SetSize(120, 24)
  close:SetText("Später")
  close:SetScript("OnClick", function() panel:Hide() end)
  panel.closeBtn = close
end

function AICompanion.UI.ShowExportPrompt(reason)
  AICompanion.UI.Init()
  local L = AICompanion.L or {}
  local title = L.EXPORT_TITLE or "AI Companion – Export"
  local msgT  = L.EXPORT_MSG or "Daten exportieren (%s)? Das UI lädt kurz neu."
  local btnT  = L.EXPORT_NOW or "Jetzt exportieren"
  local laterT= L.LATER or "Später"
  panel.title:SetText(title)
  panel.text:SetText(string.format(msgT, reason or (L.MANUAL or "manuell")))
  panel.exportBtn:SetText(btnT)
  if panel.closeBtn then panel.closeBtn:SetText(laterT) end
  panel:Show()
end

-- Tipps-Panel
local function buildReco()
  if recoFrame then return end
  recoFrame = CreateFrame("Frame", "AICompanionRecoFrame", UIParent, "BasicFrameTemplateWithInset")
  recoFrame:SetSize(420, 320)
  recoFrame:SetPoint("CENTER")
  recoFrame:Hide()
  recoFrame.title = recoFrame:CreateFontString(nil, "OVERLAY", "GameFontHighlight")
  recoFrame.title:SetPoint("TOP", 0, -10)
  recoFrame.title:SetText("AI Companion – Tipps")

  local scroll = CreateFrame("ScrollFrame", nil, recoFrame, "UIPanelScrollFrameTemplate")
  scroll:SetSize(380, 250); scroll:SetPoint("TOP", 0, -40)
  local content = CreateFrame("Frame", nil, scroll)
  content:SetSize(380, 250); scroll:SetScrollChild(content)

  local text = content:CreateFontString(nil, "OVERLAY", "GameFontHighlightSmall")
  text:SetPoint("TOPLEFT"); text:SetJustifyH("LEFT"); text:SetWidth(360)
  recoFrame.text = text

  local btn = CreateFrame("Button", nil, recoFrame, "GameMenuButtonTemplate")
  btn:SetPoint("BOTTOM", 0, 10); btn:SetSize(160, 24)
  local L = AICompanion.L or {}
  btn:SetText(L.LATER or "Schließen")
  btn:SetScript("OnClick", function() recoFrame:Hide() end)
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
  recoFrame.title:SetText(L.RECO_TITLE or "AI Companion – Tipps")
  local tips, resolvedKey = getRecommendations(characterKey)
  local lines = {}
  for _, r in ipairs(tips or {}) do
    table.insert(lines, ("|cff00ff88•|r %s"):format(r))
  end

  if #lines == 0 then
    table.insert(lines, L.RECO_EMPTY or "Keine Tipps für diesen Charakter vorhanden.")
  end
  if resolvedKey then
    table.insert(lines, 1, ("|cff66ccff%s|r"):format(resolvedKey))
    table.insert(lines, 2, "")
  end

  recoFrame.text:SetText(table.concat(lines, "\n"))
  recoFrame:Show()
end
