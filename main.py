#!python

"""
    Il-2 multiplayer server daemon/backend program: Communicates with the IL-2 multiplayer server software, Dserver.exe,
    via TCP/IP communications (remoteconsole.py) granting the player the ability to reset the current mission,
    and load missions (program_commands.py & missions.py), change environmental variables (missionenvironment.py),
    change server-side variables (dserver_run_functions.py) on the fly, send custom mission commands,
    and play arcade games (arcade_stuka.py) with score computation and results sent to a
    high score boards webpage (high_scores.py).  A player database of people logging into the server is also saved
    (player.py).  A help menu system is also provide for the available commands (help.py).

    Program constants are stored in constants.py.
    Il-2 chat console log file parsing and handling routines are found in chatlog.py.
    Note: Mission.py contains the main mission class which contains data (i.e., variables global in scope) and
    methods for more functionality than just loading missions.

    Code written by: SCG_limbo / Bob Crane
"""

from datetime import datetime
import time

from constants import *  # important all program constants are stored in this file
from remote_console import RemoteConsoleClient  # handles DServer.exe TCP/IP communication
from mission import Mission  # handles processing of mission files and arcades
from program_commands import define_commands, process_user_commands  # program commands user can call
from help import contruct_help_message  # help related functions
from chatlogs import process_chatlogs, remove_chat_logs  # functions to process chat logs
from arcade_stuka import process_arcade_game, delete_multiple_logs_files
from dserver_run_functions import start_dserver, stop_dserver, copy_sds_config_base_to_working, write_sds_file, \
    read_sds_file, check_arcade_dserver_setting
from player import read_player_list  # player database methods; import Player so pickle loads/saves correctly
# from highscores import GameResult  # import so pickle loads/saves correctly


""" Small helper function to print time and runtime iteration count """
def print_time(iteration_):
    now = datetime.now()
    current_time = now.strftime("%H:%M")
    print(f"#{iteration_}({current_time})/ ", end='', flush=True)


if __name__ == "__main__":
    print(f"SCG_Limbo's DServer Daemon (v0.5).\nLoading base mission and starting DServer.exe...")

    """ initialize remote console -- TCP/IP routines which communicate with DServer.exe  """
    r_con = RemoteConsoleClient(DSERVER_IP, DSERVER_PORT, DSERVER_USERNAME, DSERVER_PASSWORD)

    """ initialize mission class variable -- mission class contains (almost all) data/routines for handling mission data """
    mission = Mission(IL2_BASE_DIR, IL2_MISSION_DIR, MISSION_BASENAME)
    mission.init_new_mission(BASE_MISSION_NUM)  # set up mission files for processing using mission index number (usually 0 for base mission)

    """ Initialize dserver server settings  """
    copy_sds_config_base_to_working()  # copy base sds config file to working one
    server_settings_dict, sds_lines = read_sds_file(IL2_DSERVER_WORKING_CONFIG)  # read config file (sds_lines) and create server settings dict

    """ define user program commands and console help information """
    program_cmds = define_commands(mission)
    help_str = contruct_help_message(program_cmds)  # go ahead and generate main help message string now

    """ read player database containing player aliases and IL-2 IDs """
    player_list = read_player_list(IL2_PLAYER_LIST_FILE)

    """ misc init """
    iteration = 0  # number of times main while loop has run
    print_time(iteration)

    """ Start Dserver.exe """
    # check to see if dserver settings are set correctly for arcade  game
    if mission.arcade_game and check_arcade_dserver_setting(server_settings_dict): # updates current dserver settings to correspond with arcade's dserver settings
        write_sds_file(IL2_DSERVER_WORKING_CONFIG, server_settings_dict, sds_lines)  # update server config file
        server_settings_dict, sds_lines = read_sds_file(IL2_DSERVER_WORKING_CONFIG)  # and read back in with all new settings

    dserver_proc = start_dserver(IL2_DSERVER_WORKING_CONFIG)

    """ Establish connection to DServer and flush chat logs so any previous commands are not processed """
    while not r_con.connect():  # until connect
        time.sleep(4)
    r_con.send(f"cutchatlog")  # tell Dserver to dump chat log files
    time.sleep(2)  # give some time to remove permissions on any previous chat log files for flush in next line
    remove_chat_logs()

    """ daemon parser -- run continuously until manual program termination """
    while True:
        """ Read and process chat log files and user inputted commands """
        user_commands = process_chatlogs(CHATLOG_FILES_WILDCARD, r_con, mission, player_list)  # gets user commands as list of strings
        process_user_commands(user_commands, r_con, mission, server_settings_dict, program_cmds, help_str)

        """ process arcade game """
        if mission.arcade_game:
            process_arcade_game(mission.arcade, MISSION_LOGS_WILDCARD, mission.mission_filename, r_con=r_con,
                                copy_log_files=COPY_MISSION_LOGFILES)
        else:
            delete_multiple_logs_files(False, MISSION_LOGS_WILDCARD)  # do not examine or keep mission logs for non-arcade games

        """ See if user initiated Dserver restart is required and process """
        if mission.restart_dserver and (mission.user_initiated_reset or mission.load_new_mission_flag):
            r_con.send_msg("WARNING: The server will now reboot, and you will be kicked.  Please rejoin the server.")
            time.sleep(.5)
            r_con.send(f"serverinput reboot", debug=False)
            time.sleep(8)
            stop_dserver(dserver_proc)
            mission.dserver_write_index = 0
            mission.copy_mission_to_dserver_files()
            write_sds_file(IL2_DSERVER_WORKING_CONFIG, server_settings_dict, sds_lines)  # update server config file
            server_settings_dict, sds_lines = read_sds_file(IL2_DSERVER_WORKING_CONFIG)  # and read back in with all new settings
            dserver_proc = start_dserver(IL2_DSERVER_WORKING_CONFIG)  # start dserver
            mission.restart_dserver = mission.user_initiated_reset = mission.load_new_mission_flag = False

        """ print to console number of iterations of this while loop """
        iteration += 1
        if not (iteration % 50):
            print_time(iteration)
        if not (iteration % 400):  # newline
            print('')

        """ Check if mission should be reset to base mission due to player inactivity
            and/or print warning messages to user that mission is about to reset. """
        inactivity_flag = mission.check_reset_to_base_mission(r_con, RESET_TIME, SLEEP_TIME)

        """ Initiate dserver restart if too much player inactivity or dserver communication has failed for too long """
        if inactivity_flag or (not r_con.comm_flag):
            print("Restarting Dserver....")
            stop_dserver(dserver_proc)
            copy_sds_config_base_to_working()  # restore base sds file
            mission.init_new_mission(BASE_MISSION_NUM)  # initialize mission files from one of the available missions
            dserver_proc = start_dserver(IL2_DSERVER_WORKING_CONFIG)  # start dserver

        time.sleep(SLEEP_TIME)  # sleep to reduce cpu utilization
