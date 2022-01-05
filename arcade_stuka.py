import glob
import os
import shutil
import re

from constants import MISSION_LOG_BACKUP_DIR, COPY_MISSION_LOGFILES, MISSION_FILENAME,  points, FAKE_PREFIX
from highscores import compute_score, enter_score, html_write_scores
from mission_objectives import get_mission_objectives


def delete_log_file(copy_file, log_file, backup_dir=MISSION_LOG_BACKUP_DIR):
    """ delete log file or copy it to a backup directory if keep_file is True """""
    if copy_file:  # copy chatlogs files to bak dir
        file_size = os.path.getsize(log_file)
        # preserve only log filess with meaningful content and not meaningless ones that contain
        # only an "Atype 15:" log version message of size 21 bytes
        if file_size > 0 and not file_size == 21:
            try:
                shutil.copy(log_file, backup_dir)
            except shutil.Error:
                pass
    try:
        os.remove(log_file)
    except PermissionError:  # DServer.exe is using file
        pass


def delete_multiple_logs_files(keep_files, log_files_wildcard, backup_dir=MISSION_LOG_BACKUP_DIR):
    """ delete or move mission logs after they are processed """""
    filenames = glob.glob(log_files_wildcard)
    for f in filenames:
        delete_log_file(keep_files, f, backup_dir)


def two_points_close(p1, p2, error):
    """
        Determines if two object positions within IL-2 mission are close enough in distance to each other
        Input:  'x,y,z' string (e.g., '29470.2305,108.5850,21137.8516') and error amount (float)
        Returns: True or False
    """
    from math import dist

    # converts each coordinate to a list of 3 floating point numbers
    x = p1.split(',')
    p1 = [float(x[0]), float(x[1]), float(x[2])]
    x = p2.split(',')
    p2 = [float(x[0]), float(x[1]), float(x[2])]

    distance = dist(p1, p2)

    if distance < error:
        return True
    else:
        return False


class ArcadePlayer:
    """Player plane and character data """
    def __init__(self, _alias,  _player_id_str, _profile_id_str, _plane_type, _plane_id, _pilot_char_id):
        self.alias = _alias  # player alias
        self.il2_player_id = _player_id_str  # player permanent game ID assigned by IL-2 company
        self.il2_profile_id = _profile_id_str  # player login ID associated with current player chosen alias
        self.plane_type = _plane_type  # string description of plane player is flying
        self.plane_id = _plane_id  # mission logfile runtime ID number of plane found in mission logs
        self.char_id = _pilot_char_id  # mission logfile  runtime ID number of the pilot's human game model

        # player's plane damage and destroyed status
        self.plane_damaged = 0.0
        self.plane_destroyed = False

        # player pilot character's health and status
        self.damaged = 0.0
        self.killed = False
        self.ejected = False

    def print(self):
        print(f"Player attributes: alias: {self.alias}, plane type: {self.plane_type}, plane ID: {self.plane_id}, char ID: {self.char_id}: {self.plane_damaged}, {self.plane_destroyed}")


def create_player(line_str):
    """ Creates and returns a Player object from the input string information """
    plane_id = int(re.search(r'(?<=PLID:)\d+(?= )', line_str).group())
    pilot_char_id = int(re.search(r'(?<= PID:)\d+(?= BUL)', line_str).group())
    player_id_str = re.search(r'(?<= IDS:)\w+-\w+-\w+-\w+-\w+(?= )', line_str).group()
    profile_id_str = re.search(r'(?<= LOGIN:)\w+-\w+-\w+-\w+-\w+(?= )', line_str).group()
    player_alias = re.search(r'(?<= NAME:).+(?= TY)', line_str).group()
    plane_type = re.search(r'(?<= TYPE:).+(?= CO)', line_str).group()
    return ArcadePlayer(player_alias, player_id_str, profile_id_str, plane_type, plane_id, pilot_char_id)


class Vehicle:
    """Contains vehicle information from a mission file """
    def __init__(self, _name, _vehicle_type, _obj_id, _linked_id):
        self.name = _name  # scenario designer's vehicle name in mission file
        self.full_name = _name  # descriptive type name as define in log file -- not the same as self.type
        self.type = _vehicle_type  # type name as defined in mission file
        self.obj_id = _obj_id
        self.link_id = _linked_id
        self.run_id = -1  # run time id of object written to the mission  log files
        self.damage = 0.0  # damage percentage (0.0 to 1.0)
        self.destroyed = False
        # player was responsible for at least part of the damage, if so then award kill for fully destroyed vehicle>
        self.player_damaged = False
        self.score = points[self.type]

    def print(self):
        print(f"Vehicle: {self.name}, {self.full_name}, ID:{self.run_id}, PLayer_damaged: {self.player_damaged} Damage: {self.damage}, Destroyed: {self.destroyed},"
              f" Value: {self.score}")


def get_vehicles(mission_filename):
    """
        Creates the vehicles objects from the mission file
        Vehicle objects of interest are identified with m[num]_name  (e.g., 'm03_t34')

        Returns vehicle objects list and a lookup table to those objects

    """

    with open(mission_filename, 'r', encoding="UTF-8") as file:
        mission_str = file.read()

    vehicles_str = re.findall(r'\nVehicle\n{[\s\S]+?}', mission_str)
    vehicles = []
    for v in vehicles_str:
        search_result = re.search(r'(?<=Name = ")m\d\d_.+(?=";)', v)
        if search_result is not None:  # only process vehicles defined in name_regex (e.g., 'm03_t34')
            name = search_result.group()
            vtype = re.search(r'(?<=vehicles\\).+(?=\.txt";)', v).group()
            obj_id = int(re.search(r'(?<=Index = )\d+(?=;)', v).group())
            linked_id = int(re.search(r'(?<=LinkTrId = )\d+(?=;)', v).group())
            vehicles.append(Vehicle(name, vtype, obj_id, linked_id))

    veh_lookup = {}  # associate vehicle name with its index in vehicles objects for quick dictionary lookup in future
    for v in vehicles:
        veh_lookup[v.name] = v
    # print(veh_lookup)

    return vehicles, veh_lookup


class ArcadeMission:
    """ Contains data and methods associated with the current arcade game """
    def __init__(self, mission_name, mission_briefing):
        # mission objectives with lookup table to them
        self.objectives, self.m_objs = get_mission_objectives(mission_name, mission_briefing)

        self.vehicles = None  # vehicles that can be dsetroyed by player
        self.vehicle_lookup = {}  # lookup table to these vehicles
        self.veh_runtime_lookup = {}  # ID number assigned to vehicles in game as they spawn in in the mission logs

        self.player = None  # data associated with the player like plane type and damage to it and pilot character

        self.running = False  # player actively playing arcade


def process_arcade_game(arcade, mission_log_file_wildcard, keep_log_files, r_con):
    """ Parse Mission log files and run arcade """
    mlog_files = glob.glob(mission_log_file_wildcard)
    mlog_files.sort(key=lambda x: os.path.getmtime(x))  # sort by creation time/date to ensure processing from old to new
    for m in mlog_files:
        with open(m, 'r', encoding="UTF-8") as file:
            lines = file.readlines()

        # player_exited is used to make sure that the rest of the log file is processed after a
        # player exit (AType:4) is detected.  Captures special case where pilot ejects but then dies before chute opens.
        player_exited = False

        for line in lines:
            #  ignore log activity unless player has spawned and the arcade game is actively being played
            if not ('AType:10 ' in line) and not arcade.running and not player_exited:
                continue

            if 'AType:10 ' in line:  # player spawn
                """
                    player spawned in a plane; if player spawned is in the PlayerStart as defined by a mission objective
                    'PlayerStart' then create player and vehicles objects and start arcade game
                """
                position_str = re.search(r'(?<= \()\d+\.\d+,\d+\.\d+,\d+\.\d+(?=\))', line).group()

                if two_points_close(position_str, arcade.m_objs['PlayerStart'].coordinates, 10.0):
                    #  Player spawned in the arcade start area and arcade game begins; else player spawned in another
                    # area
                    arcade.veh_runtime_lookup = {}  # look up vehicles by their runtime ID given in mission logfiles
                    arcade.vehicles, arcade.veh_lookup = get_vehicles(MISSION_FILENAME)  # get enemy target vehicles with lookup
                    arcade.player = create_player(line)
                    arcade.running = True
                    log_str = re.search(r'(?<=missionReport)[\s\S]+(?=.txt)', m).group()
                    print(f"Player {arcade.player.alias} started mission in log: {log_str} flying {arcade.player.plane_type}.")
                    # player.print()

            elif 'AType:4' in line:  # player exit
                pilot_char_id = int(re.search(r'(?<= PID:)\d+(?= BUL)', line).group())
                if pilot_char_id == arcade.player.char_id:
                    arcade.running = False
                    log_str = re.search(r'(?<=missionReport)[\s\S]+(?=.txt)', m).group()
                    print(f"Player {arcade.player.alias} exited mission in log:  {log_str}\n")
                    player_exited = True  # make sure all messages in this file continue to be processed

            elif 'AType:8 ' in line:  # mission objective spawned
                pass

            elif 'AType:18 ' in line:  # pilot ejection
                pilot_id = int(re.search(r'(?<= BOTID:)\d+(?= )', line).group())
                if pilot_id == arcade.player.char_id:
                    arcade.player.ejected = True

            elif 'AType:12 ' in line:  # vehicle spawned in
                v_id = int(re.search(r'(?<= ID:)\d+(?= TY)', line).group())
                v_type = re.search(r'(?<= TYPE:).+(?= CO)', line).group()
                v_name = re.search(r'(?<= NAME:).+(?= PID)', line).group()
                try:
                    vehicle = arcade.veh_lookup[v_name]
                except KeyError:  # object spawned is not defined in mission file so ignore
                    pass
                else:
                    vehicle.full_name = v_type
                    vehicle.run_id = v_id
                    arcade.veh_runtime_lookup[v_id] = vehicle
                    # vehicle.print()

            elif 'AType:2 ' in line:  # attacker ID damaged target ID
                # print(f"damage string: {line}")
                dmg_amount = float(re.search(r'(?<= DMG:)\d+\.\d+(?= AID)', line).group())  # damage percentage from 0.0 to 1.0
                attacker_id = int(re.search(r'(?<= AID:)-*\d+(?= TID)', line).group())
                target_id = int(re.search(r'(?<= TID:)\d+(?= POS)', line).group())
                # print(f"Damage--amount: {dmg_amount} attacker_id: {attacker_id}  target_id: {target_id} in file {m}")

                if arcade.player.plane_id:  # process only if player plane defined
                    if target_id == arcade.player.plane_id:  # player plane received damage -- only update player damage
                        arcade.player.plane_damaged += dmg_amount
                    elif target_id == arcade.player.char_id:  # player human pilot character received damage
                        arcade.player.damaged += dmg_amount
                    elif attacker_id == arcade.player.plane_id:  # player did damage to a vehicle
                        try:
                            vehicle = arcade.veh_runtime_lookup[target_id]
                        except KeyError:
                            # print(f"KeyError from key: {target_id}")
                            pass
                        else:
                            vehicle.damage += dmg_amount
                            vehicle.player_damaged = True

            elif 'AType:3 ' in line:  # attacker ID killed target ID
                # print(f"kill: {line}", end='')
                attacker_id = int(re.search(r'(?<= AID:)-*\d+(?= TID)', line).group())
                target_id = int(re.search(r'(?<= TID:)\d+(?= POS)', line).group())
                if target_id == arcade.player.plane_id:
                    arcade.player.plane_destroyed = True
                elif target_id == arcade.player.char_id:
                    # print(f"Player {arcade.player.char_id} killed.")
                    arcade.player.killed = True
                else:
                    try:
                        vehicle = arcade.veh_runtime_lookup[target_id]
                    except KeyError:  # mission object that is not scored (e.g., friendly vehicles to player)
                        pass
                    else:
                        vehicle.destroyed = True
                        if attacker_id == arcade.player.plane_id:  # player did damage to a vehicle
                            vehicle.player_damaged = True

        if not keep_log_files:
            delete_log_file(COPY_MISSION_LOGFILES, m)

        if player_exited:
            """ compute damage and update high scores database """
            score, message = compute_score(arcade.player, arcade.vehicles)
            print(message)
            if r_con:  # write scores; else ignore for debugging
                r_con.send_msg(message)  # send score to console
                r_con.send_msg(f"Type {FAKE_PREFIX}reset to play again if mission not already resetting.")
                enter_score(score, message, arcade.player)  # store score in scoring database
                html_write_scores()  # write scores to html file and upload to web


def main():
    """ testing & debugging code """
    from mission import Mission
    from constants import IL2_BASE_DIR, IL2_MISSION_DIR, MISSION_BASENAME
    mission = Mission(IL2_BASE_DIR, IL2_MISSION_DIR, MISSION_BASENAME)
    file_wildcard = r'\\JUNEKIN\il2\data\logs\mission\bak5\m*.txt'
    if mission.arcade_game:
        process_arcade_game(mission.arcade, file_wildcard, True, None)


if __name__ == "__main__":
    main()
