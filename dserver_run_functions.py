""" functions related to starting and stopping dserver.exe etc."""

import subprocess
import os
from constants import IL2_DSERVER_DIR, IL2_DSERVER_EXE


def start_dserver(config_filename):
    """
        starts dserver.exe
        config_filename = name of configuration file to pass into dserver.exe
    """
    print("Dserver.exe load:  chdir to ", IL2_DSERVER_DIR, " exe: ", IL2_DSERVER_EXE, " config:", config_filename)
    os.chdir(IL2_DSERVER_DIR)  # change the directory to where dserver.exe is located since dserver cannot handle sds path and/or filenames containing spaces (yes...this is lame)
    return subprocess.Popen([IL2_DSERVER_EXE, config_filename])


def stop_dserver(dserver_process):
    return dserver_process.terminate()



