"""
    Utility to substitute source planes definition given in a source file into all the airfields in a mission file.
    To create source plane text file, select  an airfiled group (e.g., 'base_fakefield.group') and remove extraneous
    airfield data before and after the planes list.

    Full list of steps to make this work:
    1. open il2 scenario editor and (a) import fakefield object (e.g., "basefakefield.group), modify/add planes to  fakefield object, (c) export and overwrite to the same group file or a different one
    2. create plane text file used by this script:
         open group file (e.g., "basefakefield.group) and delete the preliminary airifeld information at the top and the bottom of the file (first 21 lines and like last 10 lines)  (i should automate this)
    3. run this script after plane!
    4. Run resaver.exe batch file in the (il2/bin directory) for all of the affected missions as defined by mission_names.
    5. copy mission files to server destination using copy_scenario.py script


"""
import re

plane_sourcefile = r'J:\SteamLibrary\steamapps\common\IL-2 Sturmovik Battle of Stalingrad\data\Template\bob objects\all_planes.txt'
base_dir = r'J:\SteamLibrary\steamapps\common\IL-2 Sturmovik Battle of Stalingrad\data\Multiplayer\Dogfight\scg multiplayer server' + '\\'
mission_ext = '.mission'
mission_names = ('kuban_main',
                 'kuban_convoy_attack',
                 'levelbombing',
                 'stalingrad_tanks1',
                 'air_test')

# read plane source file
with open(plane_sourcefile, encoding="UTF-8") as file_object:
    planes_str = file_object.read()


for mission_name in mission_names:
    mission_filename = base_dir + mission_name + mission_ext  # IL-2 Mission File
    write_filename = None  # replace mission sourcefile
    # write_filename = base_dir + 'yyy.mission'  # output file

    # read mission file
    with open(mission_filename, encoding="UTF-8") as file_object:
        mission_str = file_object.read()

    planes_regexp = r'Planes\n\s+\{[\s\S]+?\}\n\s+\}'  # regular expression to match all "Planes" definitions listed in mission file

    num_planes = len(re.findall(planes_regexp, mission_str))  # determine # of airfieds that need to be updated
    print('total number of planes objects: ', num_planes)

    for i in range(num_planes):
        # print(i, ":")
        plane_iter = re.finditer(planes_regexp, mission_str)  # get all planes start and end indexes; need to repeat due to unprocessesed indexes changing each time a substitution is made
        planes = list(plane_iter)  # make indexible
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
        p = p.replace("\\", "\\\\")  # substitution string needs to have backslashes preceded by an additional one for the re.sub function to work correctly below  -- quirk of python re libary
        x_str = re.sub(planes_regexp, p, mission_str[start:end])
        mission_str = mission_str[:start] + re.sub(planes_regexp, p, mission_str[start:end]) + mission_str[end + 1:]


    # write file
    if not write_filename:
        write_filename = mission_filename
    with open(write_filename, "w", encoding="UTF-8") as file_object:
        file_object.write(mission_str)
    print("New plane written to mission file ", write_filename)
