import glob
import os
import shutil
import re
import time

from constants import MISSION_LOG_BACKUP_DIR, points, FAKE_PREFIX, \
    HIGHSCORES_URL, SCORING_MILESTONES, AIR_SPAWNS,  SCORES_DB, HTML_FILE
from highscores import compute_score, enter_score, html_write_scores
from mission_objectives import get_mission_objectives, print_mission_objectives


def delete_log_file(copy_file, log_file, backup_dir=MISSION_LOG_BACKUP_DIR, do_not_delete=False):
    if do_not_delete:  # for debug purposes
        return

    """ delete log file or copy it to a backup directory if keep_file is True """""
    if copy_file:  # copy chatlogs files to bak dir
        file_size = os.path.getsize(log_file)
        # preserve only log files with meaningful content and not meaningless ones that contain
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


def delete_multiple_logs_files(keep_files, log_files_wildcard, backup_dir=MISSION_LOG_BACKUP_DIR, do_not_delete=False):
    if do_not_delete:  # debug is on
        return()

    """ delete or move mission logs after they are processed """""
    filenames = glob.glob(log_files_wildcard)
    for f in filenames:
        delete_log_file(keep_files, f, backup_dir)

def get_position_str(line):
    """ Returns a position string used by two_points_close function """
    return re.search(r'(?<=\()\d+\.\d+,\d+\.\d+,\d+\.\d+(?=\))', line).group()

def find_mission_objective(p1, mission_objectives, error=5.0):
    """ Find index in mission objectives """
    for i, m in enumerate(mission_objectives):
        if two_points_close(p1, m.coordinates, error):
            return True, i
    print("Failed to find mission objective in find_mission_objective. (Spectator spawn?)")
    return False, -1

def two_points_close(p1, p2, error, debug=False):
    """
        Determines if two object positions within IL-2 mission are close enough in distance to each other
        Input:  two 'x,y,z' strings (e.g., '29470.2305,108.5850,21137.8516') and error amount (float)
        Returns: True or False
    """
    from math import dist

    if debug:
        print("two points debug; returning true")
        return True

    # converts each coordinate to a list of 3 floating point numbers
    x = p1.split(',')
    p1 = [float(x[0]), float(x[1]), float(x[2])]
    x = p2.split(',')
    p2 = [float(x[0]), float(x[1]), float(x[2])]

    distance = dist(p1, p2)
    # print(f"distance={distance}; error={error}")

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
    player_id_str = re.search(r'(?<= LOGIN:)\w+-\w+-\w+-\w+-\w+(?= )', line_str).group()
    profile_id_str = re.search(r'(?<= IDS:)\w+-\w+-\w+-\w+-\w+(?= )', line_str).group()
    player_alias = re.search(r'(?<= NAME:).+(?= TY)', line_str).group()
    plane_type = re.search(r'(?<= TYPE:).+(?= CO)', line_str).group()
    return ArcadePlayer(player_alias, player_id_str, profile_id_str, plane_type, plane_id, pilot_char_id)


def update_player(line_str, player):
    """ Handles second and subsequent spawns """
    player.char_id = int(re.search(r'(?<= PID:)\d+(?= BUL)', line_str).group())
    print(f"in update player, pid={player.char_id}")
    player.plane_id = int(re.search(r'(?<=PLID:)\d+(?= )', line_str).group())
    player.plane_type = re.search(r'(?<= TYPE:).+(?= CO)', line_str).group()


def get_player_id_str(line_str):
    """ Retrun IL-2 permanent ID """
    return re.search(r'(?<= LOGIN:)\w+-\w+-\w+-\w+-\w+(?= )', line_str).group()


class Vehicle:
    """Contains vehicle information from a mission file """
    def __init__(self, _name, _vehicle_type, _obj_id, _linked_id, counting_id):
        self.name = _name  # scenario designer's vehicle name in mission file
        self.full_name = _name  # descriptive type name as define in log file -- not the same as self.type
        self.type = _vehicle_type  # type name as defined in mission file
        self.obj_id = _obj_id
        self.link_id = _linked_id
        self.run_id = -1  # run time id of object written to the mission  log files
        self.damage = 0.0  # total damage percentage (0.0 to 1.0)
        self.damage_by_player = 0.0 # explicit damage caused by player
        self.damage_self = 0.0  # explicit self damage (-1 attacker ID)
        self.damage_by_other = 0.0  # explict damage by others)
        self.destroyed = False
        self.player_damaged = False  # player did damage to vehicle
        self.killed_by_player = False  # player dealt killing blow to vehicle
        self.score = points[self.type]
        self.count_id = counting_id  #  assigned id # for high score printout to distinguish the different vehicles from each other

    def print(self):
        print(f"Vehicle: {self.name}, {self.full_name}, ID:{self.run_id}, PLayer_damaged: {self.player_damaged} Damage: {self.damage}, Destroyed: {self.destroyed},"
              f" Value: {self.score}")
    def short_print(self):
        print(f"Vehicle: {self.name}, {self.full_name}, ID:{self.run_id}, Value: {self.score}")


def read_vehicles(mission_filename):
    """
        Creates the vehicles instances from the mission file
        Vehicle objects of interest are identified with m[num]_name  (e.g., 'm03_t34')

        Returns vehicle objects list and a lookup table to those objects
    """

    with open(mission_filename, 'r', encoding="UTF-8") as file:
        mission_str = file.read()

    vehicles_str = re.findall(r'\nVehicle\n{[\s\S]+?}', mission_str)  # return all 'Vehicle {...}' blocks of text
    vehicles = []
    vehicle_count = 0
    for v in vehicles_str:
        search_result = re.search(r'(?<=Name = ")m\d\d_.+(?=";)', v)
        if search_result is not None:  # only process vehicles defined in name_regex (e.g., 'm03_t34')
            vehicle_count += 1
            name = search_result.group()
            vtype = re.search(r'(?<=vehicles\\).+(?=\.txt";)', v).group()
            obj_id = int(re.search(r'(?<=Index = )\d+(?=;)', v).group())
            linked_id = int(re.search(r'(?<=LinkTrId = )\d+(?=;)', v).group())
            vehicles.append(Vehicle(name, vtype, obj_id, linked_id, vehicle_count))

    veh_lookup = {}  # associate vehicle name with its index in vehicles objects for quick dictionary lookup in future
    for v in vehicles:
        veh_lookup[v.name] = v
    # print(veh_lookup)

    return vehicles, veh_lookup


class ArcadeMission:
    """ Contains data and methods associated with the current arcade game """
    def __init__(self, mission_name, mission_briefing):
        # mission objectives with lookup table to them
        self.m_objs, self.m_objs_lookup = get_mission_objectives(mission_name, mission_briefing)

        self.vehicles = None  # vehicles that can be dsetroyed by player
        self.vehicle_lookup = {}  # lookup table to these vehicles
        self.veh_runtime_lookup = {}  # ID number assigned to vehicles in game provided at spawn in
        self.other_vehicle_dict = {-1: 'Self_Damage'}  # lookup table to associate run id with a name for 'other' vehicles that are not scored; -1 is special case which needs to be in dictionary
        self.player = None  # data associated with the player like plane type and damage to it and pilot character
        self.player_planes_id_list = [] # list of id #s for current plane and previous planes for kill and damage calculation
        self.started = False  # game has started
        self.game_over = False  # game  has finished
        self.spawn_names = AIR_SPAWNS.copy()  # list of spawn points in arcade game
        self.new_airspawn_scores = SCORING_MILESTONES.copy()
        self.airfield_available = 0
        self.player_exited = True  # whether player in lobby (true) or in plane (false)
        self.score = 0
        self.old_time = time.time()

def short_filename(filename):
    """ returns shortened log filename without directory path and file extension """
    return re.search(r'(?<=missionReport\()[\s\S]+(?=.txt)', filename).group()

def process_arcade_game(arcade, mission_log_file_wildcard, mission_filename, r_con=None,
                        copy_log_files=True, do_not_delete=False, backup_dir=MISSION_LOG_BACKUP_DIR, debug=False,
                        write_score=True, db_file=SCORES_DB, html_file=HTML_FILE):

    if arcade.game_over:  # so ignore and copy/delete mission logfiles
        delete_multiple_logs_files(copy_log_files, mission_log_file_wildcard, backup_dir=backup_dir,
                                   do_not_delete=do_not_delete)
        return

    """ Parse Mission log files and run arcade -- each line contains an 'Atype' which has specific meaning (see below) """
    mlog_files = glob.glob(mission_log_file_wildcard)
    mlog_files.sort(key=lambda x: os.path.getmtime(x))  # sort by creation timestamp to ensure processing from old to new
    for current_logfile in mlog_files:
        if arcade.started:
            print(f"====== {short_filename(current_logfile)} =====")


        with open(current_logfile, 'r', encoding="UTF-8") as file:
            lines = file.readlines()

        for line in lines:
            #  ignore log activity unless player has spawned in for first time which starts game
            if not ('AType:10 ' in line) and not arcade.started:
                continue

            # Player spawned in
            if 'AType:10 ' in line:
                """
                    player spawned in a plane; if player spawned is in the PlayerStart as defined by a mission objective
                    'PlayerStart' then create player and vehicles objects and start arcade game
                """

                position_str = get_position_str(line)  # coordinates of spawn in
                found, index = find_mission_objective(position_str, arcade.m_objs, 50.0)  # determine if near registered spawn point
                # print(f"airfield found?  {found}, {index}")

                if not found:  # spawned in something like a spectator spawn so ignore
                    continue

                print(f"Spawned in location: '{arcade.m_objs[index].name}'")
                arcade.player_exited = False

                if not arcade.started:  # first time spawned in; init several variables
                    print(f"START GAME in file ======{short_filename(current_logfile)}=====")
                    arcade.started = True
                    # init player and vehicle objects
                    arcade.vehicles, arcade.veh_lookup = read_vehicles(mission_filename)  # get enemy target vehicles define in mission file with lookup
                    arcade.player = create_player(line)
                    arcade.old_time = time.time()

                else:  # spawned in second and subsequent times
                    update_player(line, arcade.player)  # pilot will have a new plane and pilot ID on subsequent spawns
                    arcade.airfield_available += -1
                    # print(f"before spawn IDs: {get_player_id_str(line)} {arcade.player.il2_player_id}")
                    # check to see that another player is taking the spawn from the first spawn
                    if get_player_id_str(line) != arcade.player.il2_player_id:
                        arcade.game_over = True
                        print("Arcade error:  Not the same player spawned in subsequent spawn compared to the first spawn")
                        r_con.send_msg(f"Error: Different players playing game!  Game over. Reset mission to try again.")

                arcade.player_planes_id_list.append(arcade.player.plane_id)
                print(f"Player {arcade.player.alias} (PID={arcade.player.char_id}) started mission flying {arcade.player.plane_type} (ID={arcade.player.plane_id}) in file: ====={short_filename(current_logfile)}=====")
                print(f"Allplane ids: {arcade.player_planes_id_list}")


            # Exited: Player left aircraft in mission
            elif 'AType:4' in line:
                pilot_char_id = int(re.search(r'(?<= PID:)\d+(?= BUL)', line).group())
                if pilot_char_id == arcade.player.char_id:
                    print(f"Player {arcade.player.alias} (pid={pilot_char_id}) exited mission with {arcade.airfield_available} airspawns available in log file: ====={short_filename(current_logfile)}======")
                    arcade.player_exited = True  # make sure all messages in this file continue to be processed
                    if arcade.airfield_available == 0:
                        arcade.game_over = True


            elif 'AType:8 ' in line:  # mission objective events triggered (e.g. game over)
                # mobj_id = int(re.search(r'(?<= OBJID:)\d+(?= POS)', line).group())  # gets OBJID (object ID?) but this is a useless ID #
                """ must determine objective fired based on its position in mission """
                print(line)
                ps = get_position_str(line)
                print(f"atype 8 pos string = {ps}")
                found, index = find_mission_objective(ps, arcade.m_objs)
                if found and arcade.m_objs[index].name == "gameover":
                    print(f"Game over triggered in mission")
                    r_con.send_msg(f"GAME OVER.")
                    arcade.game_over = True

            elif 'AType:18 ' in line:  # Ejection by pilot
                pilot_id = int(re.search(r'(?<= BOTID:)\d+(?= )', line).group())
                if pilot_id == arcade.player.char_id:
                    arcade.player.ejected = True
                    arcade.player.plane_destroyed = True
                    arcade.game_over = True

            elif 'AType:12 ' in line:  # vehicle spawned in
                v_id = int(re.search(r'(?<= ID:)\d+(?= TY)', line).group())
                v_type = re.search(r'(?<= TYPE:).+(?= CO)', line).group()
                v_name = re.search(r'(?<= NAME:).+(?= PID)', line).group()
                try:
                    vehicle = arcade.veh_lookup[v_name]
                except KeyError:
                    #  other vehicle; just associate id and name for kill report (atype = 3)
                    print(f"Other vehicle found: {v_id}:{v_name}")
                    arcade.other_vehicle_dict[v_id] = v_name
                else:
                    vehicle.full_name = v_type
                    vehicle.run_id = v_id
                    arcade.veh_runtime_lookup[v_id] = vehicle
                    print("Spawned ", end='')
                    vehicle.short_print()

            elif 'AType:2 ' in line:  # Damaged: attacker ID damaged target ID
                # print(f"damage string: {line}")
                dmg_amount = float(re.search(r'(?<= DMG:)\d+\.\d+(?= AID)', line).group())  # damage percentage from 0.0 to 1.0
                attacker_id = int(re.search(r'(?<= AID:)-*\d+(?= TID)', line).group())
                target_id = int(re.search(r'(?<= TID:)\d+(?= POS)', line).group())
                # print(f"Damage--amount: {dmg_amount} attacker_id: {attacker_id}  target_id: {target_id} in file {m}")

                if arcade.started:
                    if target_id == arcade.player.plane_id:  # player plane received damage -- only update player damage
                        if not arcade.player_exited:  # IL-2 damages/destroys plane upon player exitso we must ignore this condition
                            arcade.player.plane_damaged += dmg_amount
                            print(f"PLayer plane #{arcade.player.plane_id} damaged by: {dmg_amount}. Total damage: {arcade.player.plane_damaged}")
                    elif target_id == arcade.player.char_id:  # player human pilot character received damage
                        arcade.player.damaged += dmg_amount
                        print(f"PLayer PILOT #{arcade.player.char_id} damaged by: {dmg_amount}. Total damage: {arcade.player.plane_damaged}")
                    else:  # process vehicle damage
                        try:
                            vehicle = arcade.veh_runtime_lookup[target_id]
                        except KeyError:  # vehicle is not one we care to score like a friendly unit -- this condition unlikely to be True
                            print(f"****** KeyError trying to use vehicle key in AType:2 (damage): {target_id} *****")
                        else:
                            if attacker_id in arcade.player_planes_id_list: #  == arcade.player.plane_id:  # player did damage to a vehicle
                                vehicle.damage += dmg_amount
                                vehicle.damage_by_player += dmg_amount
                                vehicle.player_damaged = True
                                #print(f"======= Player (#{attacker_id}) damaged  {vehicle.type} (#{target_id}) by {dmg_amount}.  Total damage is {vehicle.damage:.2}.=========")
                            elif attacker_id == -1:  # vehicle is doing self damage based on a previous attack
                                # print(f"==Self damage: {vehicle.type} (#{target_id}) by {dmg_amount}.  Total damage is {vehicle.damage:.2}.==")
                                vehicle.damage += dmg_amount
                                vehicle.damage_self += dmg_amount
                            else:  # another unit is doing damage to vehicle -- apparently, this condition never reached as it seems to not logged in IL-2
                                vehicle.damage += dmg_amount
                                vehicle.damage_by_other += dmg_amount
                                print(f"Error: =======Attacker ID = {attacker_id} damaged {target_id} of type {vehicle.type} by {dmg_amount}=========")

            elif 'AType:3 ' in line:  # Killed:  attacker ID killed target ID
                print(f"kill log string: {line}", end='')
                attacker_id = int(re.search(r'(?<= AID:)-*\d+(?= TID)', line).group())
                target_id = int(re.search(r'(?<= TID:)\d+(?= POS)', line).group())
                if target_id == arcade.player.plane_id:  # il-2 destroyed player's plane
                    if not arcade.player_exited:  # il-2 destroys play plane on exit so ignore
                        print(f"player's plane (#{target_id}_ was killed by #{attacker_id}) in file {short_filename(current_logfile)}.")
                        arcade.player.plane_destroyed = True
                        arcade.game_over = True
                    else:
                        print("Ignoring player plane destruction due to mission exit.")
                elif target_id == arcade.player.char_id:
                    # print(f"Player {arcade.player.char_id} killed.")
                    arcade.player.killed = True
                    arcade.game_over = True
                    print("Player was killed.")
                else:
                    try:
                        vehicle = arcade.veh_runtime_lookup[target_id]
                    except KeyError:  # mission object that is not scored (e.g., friendly vehicles to player)
                        print(f"Ignoring kill of {arcade.other_vehicle_dict[target_id]} (#{target_id})")
                    else:
                        vehicle.destroyed = True
                        if attacker_id in arcade.player_planes_id_list:  # player dealt killing blow -- check current plane (common) and previous planes (rare if ever)
                            vehicle.player_damaged = True
                            vehicle.killed_by_player = True
                            # r_con.send(f"serverinput {vehicle.type}", debug=debug) # send kill message to mission
                            print(f"player killed vehicle (#{target_id}) of type: {vehicle.full_name}/{vehicle.name}")
                        else:
                            if attacker_id == -1 and vehicle.player_damaged:
                                vehicle.killed_by_player = True
                                print(f"Vehicle {vehicle.full_name} (#{target_id}) was killed by self damage but giving player kill credit for doing partial damage in file ====={short_filename(current_logfile)}=====")
                                r_con.send(f"serverinput {vehicle.type}", debug=debug)  # send kill message to mission
                            else:  # other type
                                print(f"OTHER KILL: {arcade.other_vehicle_dict[attacker_id]} (#{attacker_id}) killed vehicle {vehicle.full_name} (#{target_id}) in file {short_filename(current_logfile)}")

        delete_log_file(copy_log_files, current_logfile, do_not_delete=do_not_delete)  # removes mission log file from active log directory and copies to backup directory if copy_log_files=True

        # check to see if new life granted
        if arcade.started and arcade.spawn_names and not arcade.player.killed and not arcade.player.ejected and not arcade.player.plane_destroyed and not arcade.game_over:
            arcade.score, tmp = compute_score(arcade.player, arcade.vehicles)
            # print(f"Running score = {arcade.score}; available spawns = {arcade.airfield_available}; airspawns = {arcade.spawn_names}; score = {arcade.new_airspawn_scores}")
            # check to see if new life earned
            if arcade.score >= arcade.new_airspawn_scores[0]:
                print(f"New spawn available; unlocking airfield: '{arcade.spawn_names[0]}'")
                time.sleep(.1)
                r_con.send(f"serverinput {arcade.spawn_names[0]}", debug=debug)  # send server message to open next airfield
                time.sleep(.3)
                r_con.send(f"serverinput {arcade.spawn_names[0]}", debug=debug)  # send twice in case first one missed by il-2
                r_con.send_msg(f"New air spawn available!")
                arcade.airfield_available += 1
                del arcade.new_airspawn_scores[0]  # update queue
                del arcade.spawn_names[0]

        if arcade.game_over:
            """ send mission to close all airfields """
            """ compute damage and update high scores database """
            print(f"game over flag; trying to send serverinput gameover (debug = {debug})")
            time.sleep(.1)
            r_con.send(f"serverinput gameover", debug=debug)
            time.sleep(.3)
            r_con.send(f"serverinput gameover", debug=debug)  # send twice in case first one missed by il-2
            time.sleep(.1)
            r_con.send_msg(f"GAME OVER.")

            score, message = compute_score(arcade.player, arcade.vehicles)
            print(message)

            # play game ending sound
            time.sleep(.3)
            if arcade.player.killed or arcade.player.ejected or arcade.player.plane_destroyed or score < 600:
                r_con.send(f"serverinput deathsound", debug=debug)
            elif score >= 600 and score < 1400:
                r_con.send(f"serverinput endsound1", debug=debug)
            elif score >= 1400 and score < 2400:
                r_con.send(f"serverinput endsound2", debug=debug)
            else:
                r_con.send(f"serverinput endsound3", debug=debug)



            r_con.send_msg(f"===  Total score for {arcade.player.alias} is {score}.  ===")
            r_con.send_msg(f"Go to {HIGHSCORES_URL} for detailed scoring information.")
            r_con.send_msg(f"Type {FAKE_PREFIX}reset to play another round.")

            if not debug or write_score:
                enter_score(score, message, arcade.player, db_file=db_file)  # store score in scoring database
                html_write_scores(db_file=db_file, html_file=html_file, unique=True)  # write scores to html file and upload to web

            break  # break out of top for loop as no more file processing needed

    #print score every 45 seconds
    current_time = time.time()
    if arcade.started and not arcade.game_over and (current_time > arcade.old_time + 45) and not debug:
        arcade.old_time = current_time
        score, message = compute_score(arcade.player, arcade.vehicles)
        time.sleep(.1)
        r_con.send_msg(f"Score: {score}")


def main():
    """ testing & debugging code which parses mission log files for arcade game processing """
    from mission import Mission
    from remote_console import RemoteConsoleClient
    from mission_objectives import print_mission_objectives

    il2_base_dir = r'\\JUNEKIN\il2' + '\\'
    il2_mission_dir = il2_base_dir + r'data\Multiplayer\Dogfight\scg multiplayer server' + '\\'
    mission_basename = 'scg_training'
    html_dir = il2_mission_dir + 'high scores' + '\\'
    html_file = html_dir + r'index.html'
    db_scores = html_dir + r'highscores.pickle'

    mission = Mission(il2_base_dir, il2_mission_dir, mission_basename)
    mission.init_new_mission(4)
    rcon = RemoteConsoleClient(0, 0, '', '', debug=True)
    file_wildcard = r'\\JUNEKIN\il2\data\logs\mission\debug\m*.txt'
    backup_dir = r'\\JUNEKIN\il2\data\logs\mission\debug\bak' + '\\'

    print_mission_objectives(mission.arcade.m_objs, short=True)

    process_arcade_game(mission.arcade, file_wildcard, mission.mission_filename, r_con=rcon,
                        backup_dir=backup_dir, do_not_delete=True, debug=True, write_score=True, db_file=db_scores,
                        html_file=html_file)


if __name__ == "__main__":
    main()
