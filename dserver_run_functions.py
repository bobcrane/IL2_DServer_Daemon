""" functions related to starting and stopping dserver.exe etc."""
import glob
import subprocess
import time
import os
from constants import IL2_DSERVER_DIR, IL2_DSERVER_EXE
from constants import MISSION_LOG_DIR, MISSION_LOGS_WILDCARD


def start_dserver(config_filename):
    """
        starts dserver.exe
        config_filename = name of configuration file to pass into dserver.exe
    """
    os.chdir(IL2_DSERVER_DIR)  # change the directory to where dserver.exe is located since dserver cannot handle sds path and/or filenames containing spaces (yes...this is lame)
    sp = subprocess.Popen([IL2_DSERVER_EXE, config_filename])
    time.sleep(15)  # wait some time for dserver to start and login to master il-2 server
    return sp



def stop_dserver(dserver_process):
    return dserver_process.terminate()


# def get_mission_files_list():
#     files = glob.glob(MISSION_LOGS_WILDCARD)
#     print(files)
