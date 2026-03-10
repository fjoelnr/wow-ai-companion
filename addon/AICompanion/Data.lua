AICompanion = AICompanion or {}
AICompanion.Data = AICompanion.Data or {}

local function safeText(value)
  if value == nil or value == "" then
    return nil
  end
  return value
end

function AICompanion.Data.BuildCharacterKey(name, realm)
  local playerName = name or UnitName("player") or "unknown"
  local realmName = realm or GetRealmName() or "unknown"
  realmName = realmName:gsub("%s+", "")
  return string.format("%s-%s", playerName, realmName)
end

function AICompanion.Data.GetLocationContext()
  local mapId = C_Map and C_Map.GetBestMapForUnit and C_Map.GetBestMapForUnit("player") or nil
  local mapInfo = mapId and C_Map.GetMapInfo and C_Map.GetMapInfo(mapId) or nil
  return {
    mapId = mapId,
    mapName = mapInfo and mapInfo.name or nil,
    zone = safeText(GetZoneText()),
    subZone = safeText(GetSubZoneText()),
    realZone = safeText(GetRealZoneText()),
  }
end

function AICompanion.Data.GetActiveQuests()
  local quests = {}
  if not C_QuestLog or not C_QuestLog.GetNumQuestLogEntries then
    return quests
  end

  local numEntries = C_QuestLog.GetNumQuestLogEntries()
  for i = 1, numEntries do
    local info = C_QuestLog.GetInfo(i)
    if info and not info.isHeader and not info.isHidden then
      table.insert(quests, {
        id = info.questID,
        title = info.title,
        isComplete = C_QuestLog.IsComplete and C_QuestLog.IsComplete(info.questID) or false,
        campaign = info.campaignID,
      })
    end
  end
  return quests
end

function AICompanion.Data.GetProfessions()
  local professions = {}
  local prof1, prof2, archaeology, fishing, cooking = GetProfessions()
  local ids = { prof1, prof2, archaeology, fishing, cooking }

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

function AICompanion.Data.BuildSnapshot()
  local playerName = UnitName("player")
  local realmName = GetRealmName()
  local spec = GetSpecialization() or 1
  local specId = GetSpecializationInfo and select(1, GetSpecializationInfo(spec)) or 0
  local _, overallIlvl, equippedIlvl = GetAverageItemLevel()
  local location = AICompanion.Data.GetLocationContext()
  local characterKey = AICompanion.Data.BuildCharacterKey(playerName, realmName)

  return {
    ts = time(),
    player = playerName,
    realm = realmName,
    characterKey = characterKey,
    class = select(2, UnitClass("player")),
    specId = specId or 0,
    level = UnitLevel("player"),
    ilvl = equippedIlvl or overallIlvl or 0,
    locale = GetLocale(),
    mapId = location.mapId,
    zone = location.zone,
    location = location,
    activeQuests = AICompanion.Data.GetActiveQuests(),
    professions = AICompanion.Data.GetProfessions(),
    fights = AICompanion.Combat and AICompanion.Combat.Flush() or {},
    gold = GetMoney(),
  }
end
