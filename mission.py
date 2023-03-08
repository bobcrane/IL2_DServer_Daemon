import glob
import shutil
import os
import subprocess
import time
from missionenvironment import MissionEnvironment  # handles weather info (e.g., winds, clouds, mission time, etc. )
from constants import CLOUD_FILES_WILDCARD, STUKA_DSERVER_SETTINGS
from arcade_stuka import ArcadeMission
from dserver_run_functions import check_arcade_dserver_setting


class Mission:
    """
        Class which hold mission data and methods including mission file handling and
        methods associated with inputted user commands.
    """
    def __init__(self, base_dir, mission_dir, mission_basename):
        self.base_dir = base_dir  # IL-2 base directory
        self.main_mission_dir = mission_dir  # main directory where Dserver runs the mission
        self.mission_basename = mission_basename  # base name of the mission DServer will call and run repeatedly

        self.il2_resaver_dir = self.base_dir + r"bin\resaver" "\\"  # resaver.exe creates the mission binary file

        """ IL-2 mission file extensions; note that the .txt is my text file that describes the mission and is not
            part of the regular IL-2 mission files """
        self.mission_file_ext = ".Mission"  # file extension name of the text file which contains the il-2 mission data
        self.briefing_file_ext = ".eng"
        self.binfile_ext = ".msnbin"  # file extension name which contains the binary data of the il-2 mission
        self.list_ext = ".list"  # file extension name which contains the dir list of foreign language briefing files
        self.language_exts = (".chs", ".fra", ".ger", ".pol", ".rus", ".spa")
        self.description_ext = ".txt"  # file extension name which contains a short description of the mission

        """ mission and briefing files in the main mission dir (e.g., scg_training.Mission and scg_training.eng """
        self.mission_filename = self.main_mission_dir + self.mission_basename + self.mission_file_ext
        self.briefing_filename = self.main_mission_dir + self.mission_basename + self.briefing_file_ext

        """ Environmental weather data is held in this class var env"""
        self.env = MissionEnvironment(CLOUD_FILES_WILDCARD)

        """ boolean reset vars: (1) reset mission only, (2) reset requires resaver.exe action, (3) new mission """
        self.user_initiated_reset = False  # whether user inputted the reset command
        self.load_new_mission_flag = False  # whether a new map needs to reloaded (or reset to its intial state)
        self.run_resaver = False  # whether resasver.exe needs to be run to create a mission binary file
        self.restart_dserver = False  # whether the dserver needs to be restarted due to server variable being toggled liking aiming assist, invulnerability, unlimited ammo, etc.

        self.old_time = time.time()  # time stamp for whether mission needs to be reset back to mission index 0

        """ The raw IL-2 mission files are stored in the "available missions" sub directory.  Parse this directory
         and store in teh AvailableMissions class object """
        self.available_mission_dir = self.main_mission_dir + "available missions" "\\"
        self.available_missions = self.get_available_missions()
        self.num_missions = len(self.available_missions)

        self.console_msg = ""  # message to print to console later

        self.description_filename = None
        # self.mission_index = self.get_current_mission_index()  # index of the current and possibly next mission
        self.mission_index = None  # index of the current mission as specified in all available missions

        self.arcade_game = None  # will hold data after mission files loaded
        self.arcade = None

        self.dserver_write_index = 0  # dserver.exe alternates between filenames ending in 0 or 1 (e.g., scg_training0 and scg_training1); this var keeps track of that

        self.time_warnings = [5, 4, 3, 2, 1]  # minute marks before end of mission used to warn players that mission is ending

    class AvailableMissions:
        """ simple class containing string data associated with the available missions """
        def __init__(self, filename_, description_, sort_key_):
            self.filename = filename_  # string representing base file name without any extensions
            self.description = description_  # string representing the description of the mission
            self.sort_key = sort_key_  # string to dictate sort order of the entire list of Missions

    def get_sortkey_description(self, filename):
        """ Assign and return the first line of a file to the sort key
            and the second+ lines to the description """
        with open(filename, 'r') as f:
            file_str = f.read()
        split_str = file_str.split('\n', 1)
        return split_str[0], split_str[1]

    def is_current_mission_arcade(self):
        """ Returns whether the current mission is an arcade game """
        with open(self.description_filename, 'r') as f:
            file_str = f.read()
        if 'Arcade Game:' in file_str:
            print("Mission is arcade game.")
            return True
        else:
            return False

    def init_mission_arcade(self):
        """ Check to see if current mission is an arcade and defines arcade class object if so """
        self.arcade_game = self.is_current_mission_arcade()  # reads from .txt mission file
        if self.arcade_game:
            self.arcade = ArcadeMission(self.mission_filename, self.briefing_filename)
        else:
            self.arcade = None

    def get_current_mission_index(self):
        """ Function to get the current working mission index on program startup """
        sortkey, description = self.get_sortkey_description(self.description_filename)

        for i, m in enumerate(self.available_missions):
            if description == m.description:
                break
        return i

    def get_available_missions(self):
        """ Return a list of the available missions (list of AvilableMission objects) tored in the available
            missions directory """
        av_mis = []  # av_mis = available missions
        mission_filenames = glob.glob(self.available_mission_dir + r"\*"
                                      + self.mission_file_ext)  # find all mission files using mission extension
        for filename_ in mission_filenames:
            file_base_name = filename_.replace(self.mission_file_ext, "")
            sort_key, description = self.get_sortkey_description(file_base_name + self.description_ext)
            av_mis.append(self.AvailableMissions(file_base_name, description, sort_key))
        av_mis.sort(key=lambda x: x.sort_key)  # sort missions based on each mission's sort_key
        return av_mis

    def list_missions(self, unused_arg):
        """ Sends to remote console (rc) a listing of the missions available for selection """
        self.console_msg = "The following missions are available:\n"
        for i, mis in enumerate(self.available_missions):
            self.console_msg += f"{i:3}: {mis.description}\n"
        self.console_msg += f"(Note: Current mission is #{self.mission_index}.)"

    def user_load_mission(self, mission_index_str):
        """ Changes the scenario to the one selected by user.  """
        try:
            index_ = int(mission_index_str)
        except ValueError:
            self.console_msg = f"Input of '{mission_index_str}' is not a valid mission index.\n" \
                               f"Input only a single integer value between 0 and {self.num_missions - 1}."
            return
        if index_ < 0 or index_ > self.num_missions - 1:
            self.console_msg = f"Mission index value of '{index_}' is not between 0" \
                               f" and {self.num_missions - 1}"
            return
        else:
            self.console_msg = f"Next mission will be scenario #{index_}: {self.available_missions[index_].description}"
            self.mission_index = index_
            self.load_new_mission_flag = True
            return

    def reset_cmd(self, unused_str):
        """ User initiated reset command """
        self.user_initiated_reset = True
        self.console_msg = ""  # save reset specific messages for later processing
        return

    # def server_cmd(self, command_str):
    #     """ User initiated server command """
    #     rc.send(f"serverinput {command_str}")
    #     self.console_msg = f"Sending command {command_str}"
    #     return

    def init_new_mission(self, index):
        """ Initiates a new mission in preparation for new DServer startup """
        self.mission_index = index  # mission to be loaded from available missions
        self.dserver_write_index = 0
        self.load_new_mission()
        self.copy_mission_to_dserver_files()  # copy mission files to the ones actually read by dserver.exe -

    def update_mission_vars(self):
        """ updates mission variables after in new load and after files have been copied """
        self.env.open_mission_file(self.mission_filename)
        self.env.open_briefing_file(self.briefing_filename)
        self.init_mission_arcade()
        self.old_time = time.time()

    def load_new_mission(self):
        """
            selects a mission from the 'available missions' directory using mission_index and copies and renames
            mission files to generic mission basename (e.g.,  x.Mission -> scg_training.Mission, etc).
            and updates missions vars like mission and english instructions and arcade status and updates
            mission .lst file
        """

        # Copy and rename mission files
        print(f"Loading mission #{self.mission_index}....")
        mission_files = glob.glob(self.available_missions[self.mission_index].filename + ".*")  # e.g., kuban_main.Mission, kuban_main.eng, etc. and this includes full absolute path
        basename = os.path.basename(self.available_missions[self.mission_index].filename)  # e.g., ...\available_mission\kuban_main.Mission -> kuban_main
        for filename in mission_files:
            original_basename = os.path.basename(filename)  # get only the filename without directory path to it
            if self.description_ext not in filename:  # don't copy a file ending in ".txt" since it is not part of an official il-2 mission file set
                shutil.copyfile(filename, self.main_mission_dir + original_basename.replace(basename, self.mission_basename))  # e.g., kuban_main.Mission -> scg_training.Mission
            else:
                self.description_filename = filename

        # modify mission's list file to contain correct mission basename and rewrite it
        list_file = self.main_mission_dir + self.mission_basename + self.list_ext
        with open(list_file, 'r') as file_object_:
            file_str = file_object_.read()
        file_str = file_str.replace(basename.lower(), self.mission_basename)
        with open(list_file, 'w') as file:
            file.write(file_str)

        # Update new missions variables
        self.update_mission_vars()

    def resaver(self, rc):
        """ calls MissionResaver.exe (in il2 bin/resaver directory) and does necessary mission file handling
            rc var is needed for extensive remote console messaging """

        # copy .eng over all other foreign language briefing files  -- my missions only support english language
        for file_ext in self.language_exts:
            shutil.copy(self.briefing_filename, self.main_mission_dir + self.mission_basename + file_ext)

        # change current system directory where missionresaver.exe is held because that program fails to work otherwise
        os.chdir(self.il2_resaver_dir)
        mission_text_filename = self.main_mission_dir + self.mission_basename + self.mission_file_ext
        print(f"mission text file name = {mission_text_filename}; current working dir = {os.getcwd()}")

        # and run MissionResaver.exe (aka "rs") and capture its output
        print('resaver command:' "MissionResaver.exe", "-t", "-d", self.base_dir + "data",  "-f", mission_text_filename)
        rs_process = subprocess.Popen(["MissionResaver.exe", "-t", "-d", self.base_dir + "data",  "-f",
                                       mission_text_filename], stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                      universal_newlines=True)
        rc.send_msg(f"Creating new mission binary file.  This may take a while...")
        i = 0
        while rs_process.poll() is None:
            time.sleep(5)
            i += 5
            if not (i % 20):  # print every 10 seconds
                # print(f"System ({i} secs):...processing mission files")
                rc.send_msg(f"System ({i} secs):...processing mission files")

        output, errors = rs_process.communicate()
        print('out = ', output, ' errors = ', errors)
        # check for correct completion of resaver
        if "Saving localisation data DONE" in output and "Saving binary data DONE" in output \
           and "Saving .list DONE" in output:
            print("System: Processing complete.  Mission resetting...")
            rc.send_msg(f"Processing complete.  Mission resetting...")
        else:
            rc.send_msg(f"rc, System Error: MissionResaver.exe failed processing....stopping server."
                        f" Please report error to SCG_Limbo.")
            print("System error executing MissionResaver.exe:", output, errors)
            exit(-1)

    def copy_mission_to_dserver_files(self):
        """
            Copies current mission files to the files actually called by Dserver.exe.  Dserver needs to cycle between
            two sets of mission files to prevent read/write permission errors caused by (very rare)
            copying/writing to just one set of files.
            For example, scg_training.eng -> scg_training1.eng

            Function also updates the mission .lst file to contain the correct file names.
        """

        # init vars
        basename = self.mission_basename  # shorthand var to make code more readable below
        mission_num = str(self.dserver_write_index)
        print(f"copying mission to #{mission_num} slot")

        # change to mission directory to avoid working with full file path names
        os.chdir(self.main_mission_dir)

        """ copy all necessary mission files located in mission directory """
        filenames = glob.glob(basename + '.*')
        filenames = [i for i in filenames if not ('.Mission' in i)]  # remove .Mission file from list so it is not copied
        for source in filenames:
            destination = source[:len(basename)] + mission_num + source[len(basename):]
            shutil.copy(source, destination)
        # print('$$$$$$$ copying mission files to ', basename + mission_num)

        """ modify filenames in list file to correspond with mission being used by dserver  """
        list_file = basename + mission_num + ".list"
        with open(list_file, 'r') as file_object_:
            file_str = file_object_.read()
        file_str = file_str.replace(basename + '.', basename + mission_num + '.')
        with open(list_file, 'w') as file:
            file.write(file_str)

        self.dserver_write_index = (1 + self.dserver_write_index) % 2  # cycle between 0 and 1 for next dserver mission copy

    def reset_mission(self, rc):
        """ Copy mission files to next file set that dserver will use"""
        self.copy_mission_to_dserver_files()

        """ tell dserver to issue a serverinput command to reset in mission """
        rc.send("serverinput reset")

    def check_reset_to_base_mission(self, rc, reset_time_amount, tick_delay):
        """ Checks whether there is too much inactivity on server.
            Sends warning messages to console if too much inactivity detected.
            And then returns whether dserver needs to be restarted  """
        time_now = time.time()
        time_elapsed = time_now - self.old_time

        # Send warning message to user if mission is about to end
        for t in self.time_warnings:
            warning_time = reset_time_amount - (60 * t)
            if (time_elapsed >= warning_time) and (time_elapsed <= warning_time + tick_delay):
                rc.send_msg(f"System warning: Resetting mission in {t} minute{'' if t == 1 else 's'} due to player inactivity. To cancel, type any text into chat to demonstrate activity.")
                print(f"System: Resetting mission in {t} minute{'' if t == 1 else 's'}.")

        # reset mission if too much player inactivity
        if time_elapsed > reset_time_amount:
            print("Resetting server to default mission due to player inactivity.")
            return True
        else:
            return False


def main():
    """ update the server mission (e.g., scg_training.msnbin and associated files)  to the one specified by index of the available missions directory
        useful for force updating the mission the server loads """
    from constants import IL2_BASE_DIR, IL2_MISSION_DIR, MISSION_BASENAME
    mission = Mission(IL2_BASE_DIR, IL2_MISSION_DIR, MISSION_BASENAME)
    print("num missions = ", mission.num_missions)
    for i, m in enumerate(mission.available_missions):
        print(i, m.filename)
    #
    mission.mission_index = 0
    print(f"Loading mission: {mission.mission_index}")
    mission.load_new_mission()


if __name__ == "__main__":
    main()
