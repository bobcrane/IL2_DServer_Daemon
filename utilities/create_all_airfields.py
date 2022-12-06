"""
    Script that creates multiple multiplayer airfield specifications ('fakefieldS' in il-2 scenario editor terminology)
    from a source airfield specification (i.e., single German fakefield located at .5k).
    Created airfields include: parked, runway, 1k, 2k, 3k, 4k, 5k, 6k, 7k.
    In addition, script creates corresponding Russian airfields at those altitudes including .5k
    Useful for creating all airfields which can be imported into a mission later.
"""

import re

base_dir = r'J:\SteamLibrary\steamapps\common\IL-2 Sturmovik Battle of Stalingrad\data\Template\bob objects' + '\\'
mission_filename = base_dir + r'base_fakefield.group'  # IL-2 Mission File
write_filename = base_dir + 'all_airfields.Group'  # output file
altitudes = (1000, 2000, 3000, 4000, 5000, 6000, 7000)
alt_names = ('1K', '2K', '3K', '4K', '5K', '6K', '7K')
ZPos_offset = 0
index = 3  # each airfield should have a unique index
OFFSET = 2

with open(mission_filename, encoding="UTF-8") as file_object:
    airfield_str = file_object.read()

# parked start
ZPos_offset = 0
parked_str = re.sub(r"(?<=Airfield\n{\n  Name = \")[\s\S]*?(?=\";)", 'Parked', airfield_str)
parked_str = re.sub(r"(?<=StartInAir = )\d(?=;)", '2', parked_str)
parked_str = re.sub(r"(?<=ZPos = )\d+.\d*(?=;)", f"{ZPos_offset:.2f}", parked_str)
index += 1
parked_str = re.sub(r"(?<= Index = )\d+(?=;)", str(index), parked_str)
write_str = parked_str

# runway start
runway_str = re.sub(r"(?<=Airfield\n{\n  Name = \")[\s\S]*?(?=\";)", 'Runway', airfield_str)
runway_str = re.sub(r"(?<=StartInAir = )\d(?=;)", '1', runway_str)
ZPos_offset += OFFSET
runway_str = re.sub(r"(?<=ZPos = )\d+.\d*(?=;)", f"{ZPos_offset:.2f}", runway_str)
index += 1
runway_str = re.sub(r"(?<= Index = )\d+(?=;)", str(index), runway_str)
write_str += runway_str


ZPos_offset += OFFSET
m500_str = re.sub(r"(?<=ZPos = )\d+.\d*(?=;)", f"{ZPos_offset:.2f}", airfield_str)
index += 1
m500_str = re.sub(r"(?<= Index = )\d+(?=;)", str(index), m500_str)
write_str += m500_str  # add default 500m airfield now

for i, alt in enumerate(altitudes):
    alt_str = re.sub(r"(?<=Altitude = )\d+(?=;)", str(alt), airfield_str)
    alt_str = re.sub(r"(?<=Airfield\n{\n  Name = \")[\s\S]*?(?=\";)", alt_names[i], alt_str)
    ZPos_offset += OFFSET
    alt_str = re.sub(r"(?<=ZPos = )\d+.\d*(?=;)", f"{ZPos_offset:.2f}", alt_str)
    index += 1
    alt_str = re.sub(r"(?<= Index = )\d+(?=;)", str(index), alt_str)
    write_str += alt_str

"""write soviet airfields """
XPos = 150
soviet_str = re.sub(r"(?<=Country = )\d+(?=;)", '101', write_str)
soviet_str = re.sub(r"(?<=XPos = )\d+.\d*(?=;)", f"{XPos:.2f}", soviet_str)

print("len sov str = ", len(soviet_str))
# update soviet_str indexes to new index values
old_length = len(soviet_str)
i = 0
for m in re.finditer(r'(?<= Index = )\d+(?=;)', soviet_str):
    index += 1
    soviet_str = soviet_str[:(m.start() + i)] + str(index) + soviet_str[(m.end() + i):]
    new_length = len(soviet_str)
    i += new_length - old_length
    old_length = new_length

write_str += soviet_str

with open(write_filename, "w", encoding="UTF-8") as file_object:
    file_object.write(write_str)
print("New plane written to mission file ", write_filename)
