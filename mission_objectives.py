import re


class MissionObjectives:
    """Contains mission objectives from .mission text file and briefing text file """
    def __init__(self, _name, _index, _coordinates):
        self.name = _name  # name of mission objective
        self.index = _index  # index in mission file
        self.coordinates = _coordinates  # coordinates string

    def self_str(self):
        return f"Mission Objective: name = {self.name}, index = {self.index}, coordinates = {self.coordinates}"


def get_mission_objectives(mission_filename, briefing_filename):
    """
        Get mission objective MCU (mission control unit) names and their position
        Mission MCUs (Mission Control Unit, c.f., IL-2 scenario editor, can act as variables and signal this daemon when executed in mission
        Unfortunately, the mission objective's name is not stored in the  mission text file but the english briefing text file instead.
        To get this name, lookup the 'LCName = ' index value defined in the mission objective and use that to obtain
        the name in the briefing file as it would be showed in the IL-2 mission editor
        Store the results in a mission objective objective {name: position} dictionary
    """

    with open(briefing_filename, 'r', encoding="UTF-16") as file:
        briefing_str = file.read()
    with open(mission_filename, 'r', encoding="UTF-8") as file:
        mission_str = file.read()

    m_objs = []
    # get all mission objectives defined in mission file
    m_obj_str = re.findall(r'MCU_TR_MissionObjective\n{[\s\S]+?}', mission_str)
    for m in m_obj_str:
        # get mission index
        index = int(re.search(r'(?<= Index = )\d+(?=;)', m).group())

        # get position of mission object and store in a position string
        pos_str = re.search(r'(?<= XPos = )\d+\.\d+(?=;)', m).group()
        pos_str += ',' + re.search(r'(?<= YPos = )\d+\.\d+(?=;)', m).group()
        pos_str += ',' + re.search(r'(?<= ZPos = )\d+\.\d+(?=;)', m).group()

        # get name of mission objective
        lcname = re.search(r'(?<=LCName = )\d+(?=;)', m).group()
        mobj_name_regex = r'(?<=\n' + lcname + r':)\w+(?=\n)'
        name = re.search(mobj_name_regex, briefing_str).group()
        m_objs.append(MissionObjectives(name, index, pos_str))

    lookup = {}
    for m in m_objs:
        lookup[m.name] = m

    return m_objs, lookup


def print_mission_objectives(m_objs, short=False):
    print_str = ''
    print_str += f"Mission objectives ({len(m_objs)}): "
    for m in m_objs:
        if short:
            print_str += f"'{m.name}', "
        else:
            print_str += m.self_str()
    if short:
        print_str = print_str[0:len(print_str)-2]
    print(print_str)


