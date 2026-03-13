AICompanion = AICompanion or {}
AICompanion.Combat = AICompanion.Combat or {}

function AICompanion.Combat.Flush()
  -- Midnight-safe mode: disable runtime combat hooks, return empty data.
  return {}
end
