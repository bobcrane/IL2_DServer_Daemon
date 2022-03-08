import os
import shutil
import glob
import time

from constants import FAKE_PREFIX, IL2_PLAYER_LIST_FILE, MY_LOG_FILE, KEEP_CHAT_LOGS, CHATLOG_DIR_BACKUP
from player import Player, print_player_list, update_player_list, write_player_list


def remove_chat_log_file(f):
    try:
        os.remove(f)
        # print("removed ", f)
    except PermissionError:  # DServer.exe is using file
        # print("in permission error", f)
        pass


def remove_chat_logs(files):
    """ files = list of filenames """
    # print(files)
    # time.sleep(.5)  # pauseto ensure file lockout has time to be released for deletion
    for f in files:
        if KEEP_CHAT_LOGS:  # copy chatlogs files to bak dir
            if os.path.getsize(f) > 0:  # preserve only logs with content in them
                try:
                    shutil.copy(f, CHATLOG_DIR_BACKUP)
                except shutil.Error:
                    pass
        remove_chat_log_file(f)


def write_pilot_connections(pilot_connections):
    """ Append log text data of pilot connections and exits to my personal connections log file """
    with open(MY_LOG_FILE, 'a') as file_object:
        for p in pilot_connections:
            file_object.write(p)


def process_chatlogs(files_wildcard, r_con, mission, player_list):
    """
        Reads, processes, and deletes IL-2 chat log files.
        Extracts pilot inputed commands.
        Also detects when pilots connect and disconnect and saves that info to the player database and
        pilot connects log file.
        Returns a list of user commands inputted and updates old time time stamp
    """

    r_con.send(f"cutchatlog")  # tell Dserver to dump chat log files for reading and processing


    chatlog_filenames = glob.glob(files_wildcard)
    pilot_connections = []  # list of strings of pilots connecting to server
    user_commands = []  # list of strings of inputted user commands

    for filename in chatlog_filenames:
        with open(filename, 'r', encoding="UTF-8") as file_object:
            lines = file_object.readlines()

        for line in lines:
            if "sysPilotConnected;" in line:
                mission.old_time = time.time()  # update activity
                msg = line[5:16] + ': ' + line[line.index(';') + 1:].rstrip() + " connected.\n"
                print(msg, end='')
                pilot_connections.append(msg)  # extract time stamp and pilot name only
                pilot_name = msg[msg.index(': ') + 2:msg.rindex(' ')]
                r_con.send_msg(f"Welcome {pilot_name}.  Type{FAKE_PREFIX}help for a list of system commands.")

                # get IDs of player coming in and add to player list database if needed
                try:
                    player = Player(pilot_name, r_con)
                except ValueError as e:
                    print(e)
                else:
                    if update_player_list(player, player_list):
                        write_player_list(player_list, IL2_PLAYER_LIST_FILE)
                        print_player_list(player_list)
                    else:
                        print(f"Player {player.name} found in database.")

            elif "sysPilotExit;" in line:
                mission.old_time = time.time()  # note player activity.
                msg = line[5:16] + ': ' + line[line.index(';') + 1:].rstrip() + " exited.\n"
                print(msg, end='')
                pilot_connections.append(msg)

            elif FAKE_PREFIX in line:  # ignore commands produced in help messages to avoid infinite loops
                pass
            elif "$$" in line:
                pos = line.index("$$") + 2
                user_commands.append(line[pos:].strip())  # extract server command line player in chat log

    write_pilot_connections(pilot_connections)
    remove_chat_logs(chatlog_filenames)
    return user_commands
