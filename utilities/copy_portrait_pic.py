# Script to take a specified custom photo and copy it to all  cockpits of all planes in il-2

import os
import shutil

# base directory where files will be written
base_directory = "J:\\SteamLibrary\\steamapps\\common\\IL-2 Sturmovik Battle of Stalingrad\\data\\graphics\\planes\\"
#base_directory = "J:\\tmp\\"
base_ext = "\\Textures\\custom_photo.dds"

#file to use as new cockpit portrait
pic_src_file = "C:\\Users\\Bob\\Desktop\\IL-2 Box Docs\lillas\\lillas.dds"

#make sure picture_file exists
if not os.path.exists(pic_src_file):
    print(f"File error: Cannot open \'{pic_src_file}\'")
    exit()

# get plane dirctories
plane_dirs = os.listdir(base_directory)

for plane in plane_dirs:
    pic_dest_file = base_directory + plane + base_ext
    if os.path.exists(pic_dest_file):
        shutil.copyfile(pic_src_file, pic_dest_file)
        print("+" + plane)
    else:
        print("-" + plane)

