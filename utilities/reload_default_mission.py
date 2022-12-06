""" update the server mission (e.g., scg_training.msnbin and associated files)  to the one specified by index of the available missions directory
    useful to resetting the mission  """
from mission import Mission
from constants import IL2_BASE_DIR, IL2_MISSION_DIR, MISSION_BASENAME
mission = Mission(IL2_BASE_DIR, IL2_MISSION_DIR, MISSION_BASENAME)


print("num missions = ", mission.num_missions)
for i, m in enumerate(mission.available_missions):
    print(i, m.filename)
#
mission.mission_index = 0
print(f"Loading mission: {mission.mission_index}")
mission.load_new_mission()