#!python

""" Daemon to communicate with Dserver.exe program and
    process pilot commands from console while playing Il-2 """

from datetime import datetime
import time

from constants import *  # (almost) all program constants are stored in this file
from remote_console import RemoteConsoleClient  # handles DServer.exe TCP/IP communication
from mission import Mission  # handles processing of mission files and arcades
from missionenvironment import MissionEnvironment  # handles weather info (e.g., winds, clouds, mission time, etc. )
from program_commands import define_commands, process_user_commands  # program commands user can call
from help import get_help_message  # help related functions
from player import Player, read_player_list  # player database methods; import Player so pickle loads/saves correctly
from chatlogs import process_chatlogs, remove_chat_logs  # functions to process chat logs
from arcade_stuka import ArcadeMission, process_arcade_game, delete_multiple_logs_files
# from highscores import GameResult  # import so pickle loads/saves correctly
import glob

if __name__ == "__main__":
    print("SCG_Limbo's DServer Daemon")

    """ initialize remote console, mission and environmental class objects """
    r_con = RemoteConsoleClient(DSERVER_IP, DSERVER_PORT, DSERVER_USERNAME, DSERVER_PASSWORD)
    mission = Mission(IL2_BASE_DIR, IL2_MISSION_DIR, MISSION_BASENAME)
    env = MissionEnvironment(mission.working_mission_filename, mission.working_briefing_filename, CLOUD_FILES_WILDCARD)

    """ define user program commands and console help information """
    program_cmds = define_commands(r_con, env, mission)
    help_str = get_help_message(program_cmds)  # go ahead and generate main help message string now

    """ read player database containing player aliases and IL-2 IDs """
    player_list = read_player_list(IL2_PLAYER_LIST_FILE)

    """ misc init """
    iteration = 0  # number of times main while loop has run

    """ Establish connection to DServer and flush chat logs so any previous commands are not processed """
    while not r_con.connect():  # until connect
        time.sleep(2)
    r_con.send(f"cutchatlog")  # tell Dserver to dump chat log files
    remove_chat_logs(glob.glob(CHATLOG_FILES_WILDCARD))

    """ daemon parser -- run continuously until manual program termination """
    while True:
        """ Process chat log files, user commands, and any arcade game """
        user_commands = process_chatlogs(CHATLOG_FILES_WILDCARD, r_con, mission, player_list)
        process_user_commands(user_commands, r_con, env, mission, program_cmds, help_str)

        """ process arcade game """
        if mission.arcade_game:
            process_arcade_game(mission.arcade, MISSION_LOGS_WILDCARD, False, r_con)
        else:
            delete_multiple_logs_files(False, MISSION_LOGS_WILDCARD)  # absolutely no need keep mission logs

        """ print to python console program progress """
        iteration += 1
        if not (iteration % 80):
            now = datetime.now()
            current_time = now.strftime("%H:%M:%S")
            print(f"{current_time}: {iteration}")

        """ see if mission should be reset to base mission due to player inactivity """
        mission.check_reset_to_base_mission(RESET_TIME)


        time.sleep(SLEEP_TIME)  # sleep to reduce cpu utilization

