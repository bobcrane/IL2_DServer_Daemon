""" copies an il-2 mission from source directory to destination dir and also copies over english briefing over
    other foreign language briefings """

import glob
import shutil
# scenario_name = 'arcade_stuka'
#scenario_name = 'levelbombing'
#scenario_name = 'moscow_training'
scenario_name = 'kuban_main'
#scenario_name = 'air_test'


source_dir = r"J:\SteamLibrary\steamapps\common\IL-2 Sturmovik Battle of Stalingrad\data\Multiplayer\Dogfight\scg multiplayer server"
dest_dir = r"\\JUNEKIN\il2\data\Multiplayer\Dogfight\scg multiplayer server\available missions"
language_exts = (".chs", ".fra", ".ger", ".pol", ".rus", ".spa")  # foreign language briefing extensions

""" copy a scenario to Junekin"""
"""copy english file over foreign language files"""
engfile = source_dir + f"\\{scenario_name}.eng"
print(engfile)
print('--')
for exts in language_exts:
    dest_file = source_dir + f"\\{scenario_name}{exts}"
    x = shutil.copy(engfile, dest_file)
    print(f"{engfile} -> {dest_file}")
print('-----------------')
sourcefiles = source_dir + f"\\{scenario_name}.*"
filenames = glob.glob(sourcefiles)
for f in filenames:
    x = shutil.copy(f, dest_dir)
    print(f"{f} -> {x}")