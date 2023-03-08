"""
    Functions related to starting and stopping dserver.exe and associated server side variables like
    unlimited ammo, invulnerability, bombing assist, and object icons.
"""

import subprocess
import time
import os
import shutil
from constants import IL2_DSERVER_DIR, IL2_DSERVER_EXE, IL2_DSERVER_BASE_CONFIG, IL2_DSERVER_WORKING_CONFIG, \
    DSERVER_AIM, DSERVER_ICONS, DSERVER_AMMO, DSERVER_INVULN, STUKA_DSERVER_SETTINGS


class ServerSettings:
    """Class to hold dserver sds config toggleable vars like unlimited ammo, object icons, etc. """

    def __init__(self, key, description, string_list):
        self.description = description
        self.key = key
        self.line_num, self.bool_value = get_bool_value(key, string_list)
        self.original_bool_value = self.bool_value  # var to remember original state after read
        self.updated = False  # flag to indicate in print if value has been changed

    def print(self):
        if self.description[-1] == 's':
            string = f"{self.description} are {onoff_str(self.original_bool_value)}."
        else:
            string = f"{self.description} is {onoff_str(self.original_bool_value)}."
        string += f" ({onoff_str(self.bool_value)} after next reset.)\n" if self.updated else "\n"
        return string

    def toggle_print(self):
        string = f"{self.description} will be set to {onoff_str(self.bool_value)}.\nReset mission to restart server with new server setting.\n"
        return string

    def toggle_bool(self):
        self.bool_value = not self.bool_value
        self.updated = True if self.bool_value != self.original_bool_value else False


def start_dserver(config_filename):
    """
        starts dserver.exe
        config_filename = name of configuration file to pass into dserver.exe
    """
    os.chdir(IL2_DSERVER_DIR)  # change the directory to where dserver.exe is located since dserver cannot handle sds path and/or filenames containing spaces (yes...this is lame)
    sp = subprocess.Popen([IL2_DSERVER_EXE, config_filename])
    time.sleep(15)  # wait some time for dserver to start and log into master il-2 server
    return sp


def stop_dserver(dserver_process):
    return dserver_process.terminate()


def open_sds_file(filename):
    """ Opens server configuration file and returns list of lines """
    with open(filename, 'r', encoding="UTF-8") as file:
        sds_data = file.read()
    return sds_data.split('\n')


def write_sds_file(filename, server_vars, lines):
    for s in server_vars.values():
        update_config_data(s, lines)
    """ Writes lines (list of strings) to sds file """
    with open(filename, 'w', encoding="UTF-8") as file:
        file.write('\n'.join(lines))


def copy_sds_config_base_to_working():
    """ Copy base sds to working sds which can be modified """
    shutil.copy(IL2_DSERVER_BASE_CONFIG, IL2_DSERVER_WORKING_CONFIG)


def update_config_data(s, lines):
    """ updates the lines data with the boolean value of server class object """
    lines[s.line_num] = s.key + ' = ' + ('true' if s.bool_value else 'false')


def get_bool_value(key, str_list):
    """
        Returns whether key has value of '= true' and returns Boolean True or False and returns line_number
        in str_list
    """
    for i, s in enumerate(str_list):
        if key in s:
            if '= true' in s:
                return i, True
            else:
                return i, False
    print(f"Error: {key} not found in sds config file.")
    exit(-1)


def onoff_str(bool_value):
    if bool_value:
        return 'ON'
    else:
        return 'OFF'


def read_sds_file(filename):
    """ Reads sds config file and initiates server class instance and returns both """
    lines = open_sds_file(filename)  # read sds config file
    server_dict = {DSERVER_AIM: ServerSettings('aimingHelp', 'Aiming help', lines),
                   DSERVER_ICONS: ServerSettings('objectIcons', 'Object icons', lines),
                   DSERVER_AMMO: ServerSettings('unlimitAmmo', "Unlimited ammo", lines),
                   DSERVER_INVULN: ServerSettings('invulnerability', 'Plane invulnerablity', lines)}
    return server_dict, lines


def check_if_server_vars_updated(server_vars):
    """ Return true if just one of the server toggable vars has been updated """
    for s in server_vars.values():
        if s.updated:
            return True
    return False


def check_arcade_dserver_setting(server_vars):
    """ Ensure arcade mission has acceptable dserver vars and update if necessary; returns whether dserver vars changed """
    for key, value in STUKA_DSERVER_SETTINGS.items():
        if value != server_vars[key].bool_value:
            server_vars[key].toggle_bool()
    return check_if_server_vars_updated(server_vars)

