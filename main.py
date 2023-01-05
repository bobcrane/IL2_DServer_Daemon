#!python

""" Il-2 multiplayer Dserver daemon program.  It communicates with Dserver simpare to the il-2 remote console program
    and processes player commands via chat the console while playing Il-2.  The program gies the ability for players to
    implement admin level command functions on the fly.
    This is the main() function of the dserver daemon software """

from datetime import datetime
import time

from constants import *  # important program constants are stored in this file
from remote_console import RemoteConsoleClient  # handles DServer.exe TCP/IP communication
from mission import Mission  # handles processing of mission files and arcades
from program_commands import define_commands, process_user_commands  # program commands user can call
from help import get_help_message  # help related functions
from chatlogs import process_chatlogs, remove_chat_logs  # functions to process chat logs
from arcade_stuka import process_arcade_game, delete_multiple_logs_files
from dserver_run_functions import start_dserver, stop_dserver
from player import read_player_list  # player database methods; import Player so pickle loads/saves correctly
# from highscores import GameResult  # import so pickle loads/saves correctly

""" Small helper function to print time and iteration count """
def print_time(iteration_):
    now = datetime.now()
    current_time = now.strftime("%H:%M:%S")
    print(f"{current_time}: {iteration_}")


if __name__ == "__main__":
    print(f"SCG_Limbo's DServer Daemon (v0.5).\nLoading base mission and starting DServer.exe...")

    """ initialize remote console -- Routines which communicate with DServer.exe  """
    r_con = RemoteConsoleClient(DSERVER_IP, DSERVER_PORT, DSERVER_USERNAME, DSERVER_PASSWORD)

    """" initialize mission class variable -- mission class contains (almost all) data/routines for handling mission data """
    mission = Mission(IL2_BASE_DIR, IL2_MISSION_DIR, MISSION_BASENAME)
    mission.init_new_mission(BASE_MISSION_NUM)  # set up mission files for processing using mission index number (usually 0 for base mission)

    """ define user program commands and console help information """
    program_cmds = define_commands(r_con, mission)
    help_str = get_help_message(program_cmds)  # go ahead and generate main help message string now

    """ read player database containing player aliases and IL-2 IDs """
    player_list = read_player_list(IL2_PLAYER_LIST_FILE)

    """ misc init """
    iteration = 0  # number of times main while loop has run
    print_time(iteration)

    """ Start Dserver.exe """
    dserver_proc = start_dserver(IL2_DSERVER_CONFIG_FILE)

    """ Establish connection to DServer and flush chat logs so any previous commands are not processed """
    while not r_con.connect():  # until connect
        time.sleep(4)
    r_con.send(f"cutchatlog")  # tell Dserver to dump chat log files
    time.sleep(2)  # give some time to remove permissions on any previous chat log files for flush in next line
    remove_chat_logs()

    """ daemon parser -- run continuously until manual program termination """
    while True:
        """ Process chat log files and user inputted commands """
        user_commands = process_chatlogs(CHATLOG_FILES_WILDCARD, r_con, mission, player_list)  # gets user commands
        process_user_commands(user_commands, r_con, mission, program_cmds, help_str)

        """ process arcade game """
        if mission.arcade_game:
            process_arcade_game(mission.arcade, MISSION_LOGS_WILDCARD, mission.mission_filename, False, r_con)
        else:
            delete_multiple_logs_files(False, MISSION_LOGS_WILDCARD)  # no longer need any mission logs

        """ print to python program console number of iterations of this while TRUE loop """
        iteration += 1
        if not (iteration % 400):
            print_time(iteration)

        """ see if mission should be reset to base mission due to player inactivity
            and/or print warning messages to user that mission is about to reset """
        restart_dserver_flag = mission.check_reset_to_base_mission(r_con, RESET_TIME, SLEEP_TIME)

        if (not r_con.comm_flag) or restart_dserver_flag:  # initiate dserver restart
            print("Restarting Dserver....")
            stop_dserver(dserver_proc)
            mission.init_new_mission(BASE_MISSION_NUM)
            dserver_proc = start_dserver(IL2_DSERVER_CONFIG_FILE)

        time.sleep(SLEEP_TIME)  # sleep to reduce cpu utilization
