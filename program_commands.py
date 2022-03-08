from constants import FAKE_PREFIX
from help import print_help_for_individual_cmds
from arcade_stuka import ArcadeMission


class ProgramCommand:
    """Class to hold all program commands and their functionality including associated help"""
    def __init__(self, commands_list, method_pointer, command_type_string, help_msg):
        self.commands = commands_list  # command aliases (e.g., temperature, temp, t)
        # function pointer to function that should called by the command  -- usually a method in the Environment class
        self.cmd_method = method_pointer
        # command type dictates how the user command will be processed (e.g., environmental, help, procedural, etc.)
        self.command_type = command_type_string
        self.help_message = help_msg  # help message to print to the console


def define_commands(r_con, env, mis):
    """
        Initialize program commands that Il-2 users can call to get help, manipulate the mission's environment, and
        mission. Stores the command's aliases, a function pointer to process the command, the command
        type (e.g., help, environmental, process, etc.), and the command's help message for the user.

        Input: r_con = RemoteConsole class object, env = Environment class object,  mission = Mission class object
        Output: Returns a list of ProgramCommands objects

    """
    prog_cmds = []
    prog_cmds.append(
        ProgramCommand(["help", "h"], r_con.send_msg, "help",
                       f"Outputs entire help message. Provide a command name to return only that command's help"
                       f" message.\n{FAKE_PREFIX}h\n{FAKE_PREFIX}help weather"))
    prog_cmds.append(
        ProgramCommand(["temperature", "temp", "t"], getattr(env, "update_temperature"), "environmental",
                       f"Sets sea level temperature of current mission to an integer value between {env.min_temp} and "
                       f"{env.max_temp} °C.\n{FAKE_PREFIX}t 10  -- sets mission temperature to 10°C"))
    prog_cmds.append(
        ProgramCommand(["time", "z"], getattr(env, "update_time"), "environmental",
                       f"Sets time of current mission to an integer value between {env.min_time} and "
                       f"{env.max_time} hours.\n{FAKE_PREFIX}time 14 -- set mission hour to 14:00 hours"))
    prog_cmds.append(
        ProgramCommand(["wind", "winds", "w"], getattr(env, "update_wind"), "environmental",
                       f"Sets the mission winds for {env.num_windalts} altitudes using the wind_speed@direction "
                       f"string format. Enter between one and {env.num_windalts} values.\n{FAKE_PREFIX}weather 5@130"
                       f"-- sets all five wind layers to 5 m/s at 130°\n{FAKE_PREFIX}w 10@240 12@255 15@270 -- 0m: 10"
                       f"m/s @ 240°, 500m: 12 m/s @ 255°, 1000m: 15 m/s @ 270°, 2000m: 5 m/s @ 270°, 5000m: "
                       f"5 m/s @ 270°"))
    prog_cmds.append(
        ProgramCommand(["turbulence", "turb"], getattr(env, "update_turbulence"), "environmental",
                       f"Sets turbulence of current mission to an integer value between {env.min_turb} and "
                       f"{env.max_turb}.\n{FAKE_PREFIX}turb 1 -- Sets turbulence in mission to 1 m/s"))
    prog_cmds.append(
        ProgramCommand(["pressure", "p"], getattr(env, "update_pressure"), "environmental",
                       f"Sets sea level pressure of current mission to a value between {env.min_pres} to"
                       f" {env.max_pres} mmHg."
                       f"\n{FAKE_PREFIX}pressure 732 -- sets pressure to 732 mmHg."))
    prog_cmds.append(
        ProgramCommand(["haze"], getattr(env, "update_haze"), "environmental",
                       f"Sets haze level of current mission to a floating point value from {env.min_haze} to "
                       f"{env.max_haze}\n{FAKE_PREFIX}haze .3 -- sets haze value to 30%."))
    prog_cmds.append(
        ProgramCommand(["list_clouds", "lc"], getattr(env, "list_cloud_data"), "environmental",
                       f"Lists the different cloud configurations available."))
    prog_cmds.append(
        ProgramCommand(["set_clouds", "clouds", "sc"], getattr(env, "update_clouds"), "environmental",
                       f"Updates the clouds to one of the clouds configurations given by the 'list_clouds' command.\n"
                       f"Provide an integer value between 0 and {env.num_clouds - 1}"
                       f"\n{FAKE_PREFIX}clouds 2 -- Updates the clouds to cloud configuration #2."))
    prog_cmds.append(
        ProgramCommand(["reset", "r"], getattr(mis, "reset_cmd"), "procedural",
                       f"Resets the current mission.  Also commits any environmental or map/scenario changes."
                       f" No arguments.\n"))
    prog_cmds.append(
        ProgramCommand(["list_missions", "lm"], getattr(mis, "list_missions"), "procedural",
                       f"Lists all available missions. No arguments.\n"))
    prog_cmds.append(
        ProgramCommand(["set_mission", "load", "sm"], getattr(mis, "update_mission"), "procedural",
                       f"Sets the next mission to one of the missions given by 'list_missions' command.\n"
                       f"Provide an integer value between 0 and {mis.num_missions - 1}"
                       f"\n{FAKE_PREFIX}sm 1 -- Sets the mission to the mission #1."))
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


def process_user_commands(user_commands, r_con, env, mission, prog_cmds, help_str):
    """ Process pilot inputted commands """

    for command in user_commands:
        if mission.new_mission or mission.user_initiated_reset:  # flush any remaining commands after reset initiated
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
        if found:
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
                    prog_cmds[index].cmd_method(cmd_arguments)  # all env. methods accept a single string
                    r_con.send_msg(f"System: {env.console_msg}")
                    #  if environmental changes have made then resaver.exe needs to run later on mission reset
                    mission.run_resaver = env.mission_files_updated  # an environment file change requires resaver
                    print(f"environmental command message:", env.console_msg)

            elif prog_cmds[index].command_type == "procedural":
                prog_cmds[index].cmd_method(cmd_arguments)
                r_con.send_msg(f"System: {mission.console_msg}")  # print to console the resulting msg
                print(mission.console_msg)
            else:
                print("Error: I should never have gotten here during processing commands.")
                exit(-1)
        else:
            r_con.send_msg(f"System error:  Command '{command}' not recognized.")
            print(f"System error: Command '{cmd_word}' not recognized.")

    """ Process three different types of mission resets """
    if mission.new_mission:  # 1
        mission.load_new_mission()
        r_con.send_msg("System: Loading new scenario and resetting....")
        mission.reset_mission(r_con)

        # read in new mission data to environment
        env.open_mission_file(mission.working_mission_filename)
        env.open_briefing_file(mission.working_briefing_filename)
        mission.new_mission = mission.run_resaver = env.mission_files_updated = False
        mission.arcade_game = mission.is_current_mission_arcade()
        if mission.arcade_game:
            mission.arcade = ArcadeMission(mission.working_mission_filename, mission.working_briefing_filename)
        else:
            mission.arcade = None


    elif mission.run_resaver and mission.user_initiated_reset:  # 2
        # save mission and briefing string data to their respective files in the working directory for processing
        env.write_mission_file(mission.working_mission_filename)
        env.write_briefing_file(mission.working_briefing_filename)

        mission.resaver(r_con)
        mission.reset_mission(r_con)
        mission.run_resaver = mission.user_initiated_reset = env.mission_files_updated = False

    elif mission.user_initiated_reset:  # 3
        r_con.send_msg("System: Resetting mission....")
        mission.reset_mission(r_con)
        mission.user_initiated_reset = False


