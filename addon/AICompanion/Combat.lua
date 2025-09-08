AICompanion = AICompanion or {}
AICompanion.Combat = AICompanion.Combat or {}

local fights = {}
local inCombat = false
local current = nil

local f = CreateFrame("Frame")
f:RegisterEvent("PLAYER_REGEN_DISABLED")
f:RegisterEvent("PLAYER_REGEN_ENABLED")
f:RegisterEvent("COMBAT_LOG_EVENT_UNFILTERED")

f:SetScript("OnEvent", function(_, event)
  if event == "PLAYER_REGEN_DISABLED" then
    inCombat = true
    current = { start=time(), events=0, interrupts=0, deaths=0, cds={}, hpot=0 }
  elseif event == "PLAYER_REGEN_ENABLED" and inCombat and current then
    inCombat = false
    current["stop"] = time()
    table.insert(fights, current)
    current = nil
  elseif event == "COMBAT_LOG_EVENT_UNFILTERED" and inCombat and current then
    local _, sub, _, srcGUID, _, _, _, dstGUID, _, _, _, spellId, spellName = CombatLogGetCurrentEventInfo()
    current.events = current.events + 1
    if sub == "SPELL_INTERRUPT" and srcGUID == UnitGUID("player") then
      current.interrupts = current.interrupts + 1
    end
    if sub == "UNIT_DIED" and dstGUID == UnitGUID("player") then
      current.deaths = current.deaths + 1
    end
    if sub == "SPELL_CAST_SUCCESS" and srcGUID == UnitGUID("player") then
      -- Beispiele großer CDs – an Klasse anpassen
      if spellId == 190319 or spellId == 32182 or spellId == 12472 then
        current.cds[spellId] = (current.cds[spellId] or 0) + 1
      end
    end
    if sub == "SPELL_HEAL" and spellName and spellName:find("Potion") and srcGUID == UnitGUID("player") then
      current.hpot = current.hpot + 1
    end
  end
end)

function AICompanion.Combat.Flush()
  local out = fights
  fights = {}
  return out
end
