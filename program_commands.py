from constants import FAKE_PREFIX
from help import print_help_for_individual_cmds
from arcade_stuka import ArcadeMission


class ProgramCommand:
    """Class to hold all program commands and their functionality including associated help"""
    def __init__(self, commands_list, method_pointer, command_type_string, short_help_str, help_msg):
        self.commands = commands_list  # command aliases (e.g., temperature, temp, t)
        # function pointer to function that should called by the command  -- usually a method in the Environment class
        self.cmd_method = method_pointer  # points to the function to execute
        # command type dictates how the user command will be processed (e.g., environmental, help, procedural, etc.)
        self.command_type = command_type_string  # e.g., help, environmental, procedural
        self.short_help_str = short_help_str
        self.help_message = help_msg  # help message to print to the console


def define_commands(r_con, mis):
    """
        Initialize program/user commands that Il-2 users can call to get help, manipulate the mission's environment, and
        mission. Stores the command's aliases, a function pointer to process the command, the command
        type (e.g., help, environmental, process, dserver, etc.), and the command's help message for the user.

        Input: r_con = RemoteConsole class object, env = Environment class object,  mission = Mission class object
        Output: Returns a list of ProgramCommands objects

    """

    prog_cmds = []
    prog_cmds.append(
        ProgramCommand(["help", "h"], r_con.send_msg, "help",
                       "This message",
                       f"Outputs entire help message. Provide a command name to return only that command's help"
                       f" message.\n{FAKE_PREFIX}h\n{FAKE_PREFIX}help winds"))
    prog_cmds.append(
        ProgramCommand(["list_missions", "list", "ls", "lm"], getattr(mis, "list_missions"), "procedural",
                       "Lists available missions",
                       f"Lists all available missions. No arguments.\n"))
    prog_cmds.append(
        ProgramCommand(["load_mission", "load", "l"], getattr(mis, "user_load_mission"), "procedural",
                       "Loads a mission",
                       f"Loads and starts the next mission to one of the missions given by 'list_missions' command.\n"
                       f"Provide an integer value between 0 and {mis.num_missions - 1}"
                       f"\n{FAKE_PREFIX}load 1 -- Loads and starts mission #1."))
    prog_cmds.append(
        ProgramCommand(["reset", "r"], getattr(mis, "reset_cmd"), "procedural",
                       "Restores a mission and implements environmental changes",
                       f"Resets the current mission.  Also commits any environmental or map/scenario changes."
                       f" No arguments.\n"))
    prog_cmds.append(
        ProgramCommand(["command", "cmd", "c"], None, "server_command",
                       "Sends a custom server command to the mission.",
                       f"Sends a server command to the mission.  Any server commands will be indicated in the mission"
                       f"briefing. Takes one argument which is the string set to the mission.  For example: cmd aihigh\n"))
    prog_cmds.append(
        ProgramCommand(["temperature", "temp", "t"], getattr(mis.env, "update_temperature"), "environmental",
                       "Sets mission temperature",
                       f"Sets sea level temperature of current mission to an integer value between {mis.env.min_temp} and "
                       f"{mis.env.max_temp} °C.\n{FAKE_PREFIX}t 10  -- sets mission temperature to 10°C"))
    prog_cmds.append(
        ProgramCommand(["time", "z"], getattr(mis.env, "update_time"), "environmental",
                       "Sets mission start time",
                       f"Sets hour start time of current mission to an integer value between {mis.env.min_time} and "
                       f"{mis.env.max_time} hours.\n{FAKE_PREFIX}time 14 -- set mission hour to 14:00 hours"))
    prog_cmds.append(
        ProgramCommand(["winds", "wind", "w"], getattr(mis.env, "update_wind"), "environmental",
                       "Changes winds aloft",
                       f"Sets the winds for the {mis.env.num_windalts} wind layers (0m, 500m, 1000m, 2000m, and 5000m). "
                       f"Each wind layer is specified using a wind_speed@direction string where wind speed is in"
                       f" m/s and direction is from 0° to 359° (e.g., 6@230) "
                       f". Enter between 1 and {mis.env.num_windalts} wind layers.\n{FAKE_PREFIX}winds 5@130"
                       f" -- Sets all five wind layers to 5 m/s at 130°\n{FAKE_PREFIX}w 10@240 12@255 15@270 -- Sets wind layers to:"
                       f"\n.           0m: 10 m/s @ 240°\n.       500m: 12 m/s @ 255°\n.     1000m: 15 m/s @ 270°\n.     2000m: 15 m/s @ 270°\n.     5000m: "
                       f"15 m/s @ 270°"))
    prog_cmds.append(
        ProgramCommand(["turbulence", "turb"], getattr(mis.env, "update_turbulence"), "environmental",
                       "Sets turbulence level",
                       f"Sets turbulence of current mission to a value between {mis.env.min_turb} and "
                       f"{mis.env.max_turb}.\n{FAKE_PREFIX}turb .5 -- Sets turbulence in mission to 0.5 m/s"))
    prog_cmds.append(
        ProgramCommand(["pressure", "pres", "p"], getattr(mis.env, "update_pressure"), "environmental",
                       "Sets barometric pressure",
                       f"Sets sea level pressure of current mission to a value between {mis.env.min_pres} to"
                       f" {mis.env.max_pres} mmHg.  Note that 760 mmHg is standard."
                       f"\n{FAKE_PREFIX}pressure 732 -- sets pressure to 732 mmHg."))
    prog_cmds.append(
        ProgramCommand(["haze", "ha"], getattr(mis.env, "update_haze"), "environmental",
                       "Sets haze level",
                       f"Sets haze level of current mission to a floating point value from {mis.env.min_haze} to "
                       f"{mis.env.max_haze}\n{FAKE_PREFIX}haze 30 -- sets haze value to 30%."))
    prog_cmds.append(
        ProgramCommand(["list_clouds", "lc"], getattr(mis.env, "list_cloud_data"), "environmental",
                       "Lists preset cloud configurations",
                       f"Lists the different cloud configurations available."))
    prog_cmds.append(
        ProgramCommand(["set_clouds", "clouds", "sc"], getattr(mis.env, "update_clouds"), "environmental",
                       "Sets clouds to a preset configuration",
                       f"Updates the clouds to one of the clouds configurations given by the 'list_clouds' command.\n"
                       f"Provide an integer value between 0 and {mis.env.num_clouds - 1}"
                       f"\n{FAKE_PREFIX}clouds 2 -- Updates the clouds to cloud configuration #2."))

    return prog_cmds


def is_cmd_in_program_commands(cmd_str, p_cmds):
    """ Determine if cmd_str (string) is contained in the list of program commands
        Returns True/False and and index into the list of program commands """
    cmd_found = False
    i = -1
    for i, c in enumerate(p_cmds):
        if cmd_str in c.commands:
            cmd_found = True
            break
    return cmd_found, i


def process_user_commands(user_commands, r_con, mission, prog_cmds, help_str):
    """ Process pilot inputted commands queue """

    for command in user_commands:
        # flush any remaining commands after reset initiated
        if mission.new_mission or mission.user_initiated_reset:
            print("reset ordered")
            break

        # separate command and any following arguments into two strings: command and arguments
        cmd = command.split(' ', 1)
        cmd_word = cmd[0]
        if len(cmd) > 1:
            cmd_arguments = cmd[1]
        else:
            cmd_arguments = ''

        # determine if cmd_word is recognized
        found, index = is_cmd_in_program_commands(cmd_word, prog_cmds)

        if not found:
            r_con.send_msg(f"Error:  '{cmd_word}' is not a recognized recognized.")
            print(f"Error:  '{cmd_word}' is not a recognized recognized.")
            return

        print(f"Player command: {cmd_word}:{cmd_arguments}")
        """Process commands depending on type (e.g., help, environmental, etc. """
        if prog_cmds[index].command_type == "help":
            if cmd_arguments:  # user has requested to print help for one or more commands
                print_help_for_individual_cmds(r_con, prog_cmds, cmd_arguments)
            else:  # otherwise print entire help message
                r_con.send_msg(help_str)

        elif prog_cmds[index].command_type == "environmental":
            if mission.arcade_game:
                r_con.send_msg("Environmental commands not allowed during arcade play.")
                print("Environmental commands not allowed during arcade play.")
            else:
                print("env cmd_arguments: ", cmd_arguments)
                flag = prog_cmds[index].cmd_method(cmd_arguments)  # all mis.env. methods accept a single string
                """ Append terminal message to remind user to reset mission to affect environmental changes """
                if mission.env.mission_files_updated and flag:
                    mission.env.console_msg += " Reset mission to put environmental changes into effect."
                r_con.send_msg(f"System: {mission.env.console_msg}")
                #  if environmental changes have made then resaver.exe needs to run later on mission reset
                mission.run_resaver = mission.env.mission_files_updated  # an environment file change requires resaver
                print(f"environmental command message xxx:", mission.env.console_msg)

        elif prog_cmds[index].command_type == "procedural":
            prog_cmds[index].cmd_method(cmd_arguments)
            r_con.send_msg(f"System: {mission.console_msg}")  # print to console the resulting msg
            print(mission.console_msg)

        # server command -- send straight to dserver
        elif prog_cmds[index].command_type == "server_command":
            if cmd_arguments:  # user has requested to print help for one or more commands
                r_con.send_msg(f"System: Sending to server mission the input command '{cmd_arguments}'.")
                r_con.send(f"serverinput {cmd_arguments}")
            else:  # otherwise print entire help message
                r_con.send_msg(f"Error: {cmd_word} requires an argument.")  # print to console the resulting msg


        else:
            print("Error: I should never have gotten here during processing commands.")
            exit(-1)

    """ Process three different types of mission resets """
    if mission.new_mission:  # a new mission is being loaded
        mission.load_new_mission()
        r_con.send_msg("System: Loading new scenario and resetting....")
        mission.reset_mission(r_con)

        # read in new mission data to environment
        mission.env.open_mission_file(mission.mission_filename)
        mission.env.open_briefing_file(mission.briefing_filename)
        mission.new_mission = mission.run_resaver = mission.env.mission_files_updated = False  # reset booleans
        mission.arcade_game = mission.is_current_mission_arcade()
        if mission.arcade_game:
            mission.arcade = ArcadeMission(mission.mission_filename, mission.briefing_filename)
        else:
            mission.arcade = None

    elif mission.run_resaver and mission.user_initiated_reset:  # 2
        # save mission and briefing string data to their respective files
        mission.env.write_mission_file(mission.mission_filename)
        mission.env.write_briefing_file(mission.briefing_filename)

        mission.resaver(r_con)
        mission.reset_mission(r_con)
        mission.run_resaver = mission.user_initiated_reset = mission.env.mission_files_updated = False

    elif mission.user_initiated_reset:  # 3
        r_con.send_msg("System: Resetting mission....")
        mission.reset_mission(r_con)
        mission.user_initiated_reset = False


