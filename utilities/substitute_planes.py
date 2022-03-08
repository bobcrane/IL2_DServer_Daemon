""" Utility to substitute source planes definition into all airfields in a mission file """
import re

plane_sourcefile = r'J:\SteamLibrary\steamapps\common\IL-2 Sturmovik Battle of Stalingrad\data\Template\bob objects\all_planes.txt'
base_dir = r'J:\SteamLibrary\steamapps\common\IL-2 Sturmovik Battle of Stalingrad\data\Multiplayer\Dogfight\scg multiplayer server' + '\\'
mission_filename = base_dir + r'kuban_main.mission'  # IL-2 Mission File
write_filename = None  # replace mission sourcefile
# write_filename = base_dir + 'yyy.mission'  # output file

# read plane source
with open(plane_sourcefile, encoding="UTF-8") as file_object:
    planes_str = file_object.read()


# read mission file
with open(mission_filename, encoding="UTF-8") as file_object:
    mission_str = file_object.read()

planes_regexp = r'Planes\n\s+\{[\s\S]+?\}\n\s+\}'  # regular expression to match all "Planes" definitions listed in mission file

num_planes = len(re.findall(planes_regexp, mission_str))  # determine # of airfieds that need to be updated
print('total number of planes objects: ', num_planes)

for i in range(num_planes):
    # print(i, ":")
    plane_iter = re.finditer(planes_regexp, mission_str)  # get all planes start and end indexes; need to repeat due to unprocessesed indexes changing each time a substitution is made
    planes = list(plane_iter)  # make indexable
    start = planes[i].start()
    end = planes[i].end()


    """ process the base planes_str to incorporate indentation, starting position, and/or altitude of original mission
        file """
    p = planes_str  # planes substitute string
    p = p[2:]  # strip out first two characters to achieve correct indentation level

    # determine indentation level and then insert correct level of indentation into the planes substitute string
    p_str = planes[i].group()
    num_leading_spaces = len(p_str[7:]) - len(p_str[7:].lstrip())  # examine first lines after 'Planes\n'
    # print('num leading spaces = ',  num_leading_spaces)
    if num_leading_spaces > 2:
        num_spaces = num_leading_spaces - 2
        spaces = ' ' * num_spaces
        # p = spaces + p  # indent first line
        p = re.sub(r'\n', r'\n' + spaces, p)  # and then insert necessary indent after each newline
        p += '\n'

    # extract StartInAir number -- 0 (in air), 1 (runway), 2 (parked) and substitute if necessary
    regexp = r'(?<=StartInAir = )\d'
    x = re.search(regexp, mission_str[start:end]).group()
    y = re.search(regexp, p).group()
    if x != y:  # need to substitute StartInAir
        p = re.sub(regexp, x, p)

    # extract altitude and substitute if necessary
    regexp = r'(?<=Altitude = )\d+'
    x = re.search(regexp, mission_str[start:end]).group()
    y = re.search(regexp, p).group()
    if x != y:  # need to substitute StartInAir
        p = re.sub(regexp, x, p)

    # do regular expression substitution
    p = p.replace("\\", "\\\\")  # substitution string needs to have backslashes preceded by an additional one for the re.sub function to work correctly below  -- python re. quirk
    x_str = re.sub(planes_regexp, p, mission_str[start:end])
    mission_str = mission_str[:start] + re.sub(planes_regexp, p, mission_str[start:end]) + mission_str[end + 1:]


# write file
if not write_filename:
    write_filename = mission_filename
with open(write_filename, "w", encoding="UTF-8") as file_object:
    file_object.write(mission_str)
print("New plane written to mission file ", write_filename)
