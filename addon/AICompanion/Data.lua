-- Data.lua – Midnight-safe data collectors.
--
-- All APIs used here are non-combat, non-secret: quests, map, bags,
-- professions, talents, item level. Safe under Patch 12.0.0 restrictions.

AICompanion = AICompanion or {}
AICompanion.Data = AICompanion.Data or {}

--- Collect the player's active quest log (names + IDs).
-- @return table Array of {id, title, isComplete}
function AICompanion.Data.GetActiveQuests()
  local quests = {}
  local numEntries = C_QuestLog.GetNumQuestLogEntries()
  for i = 1, numEntries do
    local info = C_QuestLog.GetInfo(i)
    if info and not info.isHeader and not info.isHidden then
      table.insert(quests, {
        id = info.questID,
        title = info.title,
        isComplete = C_QuestLog.IsComplete(info.questID),
      })
    end
  end
  return quests
end

--- Collect the player's profession info.
-- @return table Array of {name, skillLevel, maxLevel}
function AICompanion.Data.GetProfessions()
  local professions = {}
  local prof1, prof2, arch, fish, cook = GetProfessions()
  local ids = { prof1, prof2, arch, fish, cook }
  for _, id in ipairs(ids) do
    if id then
      local name, _, skillLevel, maxLevel = GetProfessionInfo(id)
      if name then
        table.insert(professions, {
          name = name,
          skillLevel = skillLevel,
          maxLevel = maxLevel,
        })
      end
    end
  end
  return professions
end

--- Collect current map/zone context.
-- @return table {mapId, mapName, zone, subZone}
function AICompanion.Data.GetLocationContext()
  local mapId = C_Map.GetBestMapForUnit("player")
  local mapInfo = mapId and C_Map.GetMapInfo(mapId) or nil
  return {
    mapId = mapId,
    mapName = mapInfo and mapInfo.name or nil,
    zone = GetZoneText(),
    subZone = GetSubZoneText(),
    realZone = GetRealZoneText(),
  }
end

--- Build a full session snapshot with all non-combat data.
-- Called by ExportSession() in Core.lua.
-- @return table Session object ready for SavedVariables
function AICompanion.Data.BuildSnapshot()
  local spec = GetSpecialization() or 1
  local specId = select(1, GetSpecializationInfo(spec)) or 0
  local _, overallIlvl, equippedIlvl = GetAverageItemLevel()

  return {
    ts = time(),
    player = UnitName("player"),
    class = select(2, UnitClass("player")),
    specId = specId,
    level = UnitLevel("player"),
    ilvl = equippedIlvl or overallIlvl or 0,
    locale = GetLocale(),

    -- Location
    location = AICompanion.Data.GetLocationContext(),

    -- Quests
    activeQuests = AICompanion.Data.GetActiveQuests(),

    -- Professions
    professions = AICompanion.Data.GetProfessions(),

    -- Combat windows (timestamps only – rich data comes from CombatLog.txt)
    fights = AICompanion.Combat and AICompanion.Combat.Flush() or {},

    -- Gold (copper)
    gold = GetMoney(),
  }
end
