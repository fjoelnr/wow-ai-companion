-- Combat.lua – Midnight-compatible combat state tracker.
--
-- With Patch 12.0.0 ("Addon Disarmament") COMBAT_LOG_EVENT_UNFILTERED is
-- secret during instanced/combat content. All rich combat analysis now
-- happens externally via CombatLog.txt file parsing.
--
-- The addon only tracks combat enter/leave to timestamp fight windows.
-- This data is exported via SavedVariables for the external watcher.

AICompanion = AICompanion or {}
AICompanion.Combat = AICompanion.Combat or {}

local fights = {}
local inCombat = false
local current = nil

local f = CreateFrame("Frame")
f:RegisterEvent("PLAYER_REGEN_DISABLED")
f:RegisterEvent("PLAYER_REGEN_ENABLED")

f:SetScript("OnEvent", function(_, event)
  if event == "PLAYER_REGEN_DISABLED" then
    inCombat = true
    current = {
      start = time(),
      startMs = GetTime(), -- high-resolution timestamp for matching with CombatLog.txt
    }
  elseif event == "PLAYER_REGEN_ENABLED" and inCombat and current then
    inCombat = false
    current.stop = time()
    current.stopMs = GetTime()
    current.durationSec = current.stopMs - current.startMs
    table.insert(fights, current)
    current = nil
  end
end)

--- Return true if the player is currently in combat.
function AICompanion.Combat.InCombat()
  return inCombat
end

--- Flush all recorded fights and reset the buffer.
-- @return table Array of fight records {start, stop, startMs, stopMs, durationSec}
function AICompanion.Combat.Flush()
  local out = fights
  fights = {}
  return out
end
