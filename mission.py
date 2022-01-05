import glob
import shutil
import os
import subprocess
import time
from arcade_stuka import ArcadeMission


class Mission:
    """ Class to hold data and methods associated with mission file handling and some processing
        not directly associated with environmental data (e.g., weather conditions)  """

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
        self.main_mission_filename = self.main_mission_dir + self.mission_basename + self.mission_file_ext
        self.main_briefing_filename = self.main_mission_dir + self.mission_basename + self.briefing_file_ext

        """ the mission and briefing files are stored in a working directory to not corrupt these same files
            stored in the main mission directory until they are ready for processing """
        self.working_dir = self.main_mission_dir + "current mission text files" "\\"
        self.working_mission_filename = self.working_dir + self.mission_basename + self.mission_file_ext
        self.working_briefing_filename = self.working_dir + self.mission_basename + self.briefing_file_ext

        """ boolean reset vars: (1) reset mission only, (2) reset requires resaver.exe action, (3) new mission """
        self.user_initiated_reset = False  # whether or not user inputted the reset command
        self.new_mission = False  # whether or not a new map needs to reloaded (or reset to its intial state)
        self.run_resaver = False  # whether or not resasver.exe needs to be run to create a mission binary file
        self.old_time = self.time_now = time.time()  # time stamps

        """ The raw IL-2 mission files are stored in the "available missions" sub directory.  Parse this directory
         and store in teh AvailableMissions class object """
        self.available_mission_dir = self.main_mission_dir + "available missions" "\\"
        self.available_missions = self.get_available_missions()
        self.num_missions = len(self.available_missions)

        self.console_msg = ""  # message to print to console later

        self.description_filename = self.main_mission_dir + self.mission_basename + self.description_ext
        self.mission_index = self.get_current_mission_index()  # index of the current and possibly next mission
        # Whether or not current mission is an arcade game
        self.arcade_game = self.is_current_mission_arcade()
        print(f"Current mission is an arcade game = {self.arcade_game}")

        if self.arcade_game:
            self.arcade = ArcadeMission(self.working_mission_filename, self.working_briefing_filename)
        else:
            self.arcade = None

    class AvailableMissions:
        """ very simple class containing string data associated with the available missions """
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
        """ Returns whether or not the current mission is an arcade game """
        with open(self.description_filename, 'r') as f:
            file_str = f.read()
        if 'Arcade Game:' in file_str:
            return True
        else:
            return False

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

    def list_missions(self, unused_str):
        """ Sends to remote console (rc) a listing of the missions available for selection """
        self.console_msg = "The following missions are available:\n"
        for i, mis in enumerate(self.available_missions):
            self.console_msg += f"{i:4}: {mis.description}\n"
            # print(f"{i:4}: {mis.description}")
        self.console_msg += f"(Note: Current mission index is {self.mission_index}.)"

    def update_mission(self, mission_index_str):
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
            self.new_mission = True
            return

    def reset_cmd(self, unused_str):
        """ User initiated reset """
        self.user_initiated_reset = True
        self.console_msg = ""  # save reset specific messages for later processing
        return

    def load_new_mission(self):
        """ selects a mission from the available missions directory and copies and renames these files to
            the appropriate directories and file names using the generic mission basename (e.g., scg_training). """
        """ copy all new mission files to main directory and rename them to the mission basename (e.g., 
            x.Mission -> scg_training.Mission, etc.) """
        new_mission_files = glob.glob(self.available_missions[self.mission_index].filename + ".*")
        new_basename = os.path.basename(self.available_missions[self.mission_index].filename)
        for f_ in new_mission_files:
            original_basename = os.path.basename(f_)  # get only the filename without directory path to it
            shutil.copyfile(f_, self.main_mission_dir + original_basename.replace(new_basename, self.mission_basename))

        # move .Mission file into working directory; copy .eng file into working directory as well
        shutil.move(self.main_mission_filename, self.working_mission_filename)
        shutil.copy(self.main_briefing_filename, self.working_briefing_filename)

        # modify mission's list file to contain correct mission basenames and rewrite it
        list_file = self.main_mission_dir + self.mission_basename + self.list_ext
        with open(list_file, 'r') as file_object_:
            file_str = file_object_.read()
        file_str = file_str.replace(new_basename.lower(), self.mission_basename)
        with open(list_file, 'w') as file:
            file.write(file_str)

    def resaver(self, rc):
        """ calls MissionResaver.exe and does necessary mission file handling
            rc and smg are needed for extensive remote console messaging """

        shutil.copy(self.working_mission_filename, self.main_mission_dir)  # copy .Mission file to main mission dir
        shutil.copy(self.working_briefing_filename, self.main_mission_dir)  # copy .eng file to main mission dir
        # copy .eng over all other foreign language briefing files  -- my missions only support english language
        for file_ext in self.language_exts:
            shutil.copy(self.working_briefing_filename, self.main_mission_dir + self.mission_basename + file_ext)

        # change current system directory where missionresaver.exe is held because that program fails to work otherwise
        os.chdir(self.il2_resaver_dir)
        mission_text_filename = self.main_mission_dir + self.mission_basename + self.mission_file_ext
        print(f"mission text file name = {mission_text_filename}; current working dir = {os.getcwd()}")

        # and run MissionResaver.exe (aka "rs") and capture its output
        # MissionResaver.exe must use relative paths because it fails using network paths.
        i = self.main_mission_filename.find(r"data" "\\")
        rel_path_filename = r"..\.." + "\\" + self.main_mission_filename[i:]
        print(f"rel path: {rel_path_filename}")
        rs_process = subprocess.Popen(["MissionResaver.exe", "-t", "-d", r"..\..\data", "-f",
                                       rel_path_filename], stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                      universal_newlines=True)
        print("System: Reset initiated. Processing mission files. Please be patient...")
        rc.send_msg(f"System: Reset initiated. Processing mission files. Please be patient...")
        i = 0
        while rs_process.poll() is None:
            time.sleep(5)
            i += 5
            if not (i % 10):  # print every 10 seconds
                # print(f"System ({i} secs):...processing mission files")
                rc.send_msg(f"System ({i} secs):...processing mission files")

        output, errors = rs_process.communicate()
        # check for correct completion of resaver
        if "Saving localisation data DONE" in output and "Saving binary data DONE" in output \
           and "Saving .list DONE" in output:
            print("System: Processing complete.  Mission resetting...")
            rc.send_msg(f"System: Processing complete.  Mission resetting...")
            rc.send("serverinput reset")
        else:
            rc.send_msg(f"rc, System Error: MissionResaver.exe failed processing....stopping server."
                        f" Please contact Limbo ASAP!!!")
            print("System error trying to MissionResaver.exe:", output, errors)
            exit(-1)

        # remove .Mission text file so user do not load it onto their computer; copy of this still exists in working dir
        os.remove(mission_text_filename)

    def reset_mission(self, rc):
        """ tell DServer to initiate a reset"""
        rc.send("serverinput reset")

    def check_reset_to_base(self, reset_time_amount):
        """ Reset to base mission if too much player inactivity """
        if self.mission_index != 0:
            time_now = time.time()
            if (self.old_time + reset_time_amount) < self.time_now and self.mission_index != 0:
                print("Resetting server to default mission due to player inactivity.")
                self.mission_index = 0
                self.load_new_mission()
                self.old_time = time_now
