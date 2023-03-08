from constants import FAKE_PREFIX, DSERVER_AIM, DSERVER_ICONS, DSERVER_AMMO, DSERVER_INVULN, PRINT_DSERVER_VARS
from help import print_help_for_individual_cmds
from dserver_run_functions import check_if_server_vars_updated, check_arcade_dserver_setting

class ProgramCommand:
    """Class to hold all program commands and their functionality including associated help"""
    def __init__(self, commands_list, method_pointer, command_type_string, short_help_str, help_msg):
        self.commands = commands_list  # command aliases (e.g., temperature, temp, t)
        # function pointer to function that should called by the command  -- usually a method in the Environment class
        self.cmd_method = method_pointer  # points to the function to execute or possibly other type of var
        # command type dictates how the user command will be processed (e.g., environmental, help, procedural, etc.)
        self.command_type = command_type_string  # e.g., help, environmental, procedural
        self.short_help_str = short_help_str
        self.help_message = help_msg  # help message to print to the console


def define_commands(mis):
    """
        Initialize player console commands.  Commands do things like provide help, manipulate the mission's environment, load/list different missions,
        and change server side settings. Stores the command's aliases, a function pointer to process the command (if necessary), the command
        type (e.g., help, environmental, process, dserver, etc.), and the command's help message for the user.


    """

    prog_cmds = []
    prog_cmds.append(
        ProgramCommand(["help", "h"], None, "help",
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
                       "Resets the mission.",
                       f"Resets the current mission and also executes any pilot commands affecting the mission or server."
                       f" No arguments.\n"))
    prog_cmds.append(
        ProgramCommand(["command", "cmd", "c"], None, "server_command",
                       "Sends custom mission command.",
                       f"Sends a server command to the mission.  Server commands (if any) will be indicated in the mission"
                       f"briefing. Takes one argument which is command sent to the mission.  For example: cmd aihigh\n"))
    prog_cmds.append(
        ProgramCommand(["server", "svars", "s"], PRINT_DSERVER_VARS, "dserver",
                       "Lists server side settings (see below).",
                       f"Lists server side settings like aiming assist, unlimited ammo, object icons, etc. No arguments.\n"))
    prog_cmds.append(
        ProgramCommand(["aim"], DSERVER_AIM, "dserver",
                       "Toggles aiming assist on server.",
                       f"Turns on/off server side aiming assist. No arguments.\n"
                       f"Note that pilot can manually turn on/off aiming assist if server is permitting aiming assist (default: RCtrl-I).\n"
                       f"Reset mission to have server restart with this new setting."))
    prog_cmds.append(
        ProgramCommand(["icons"], DSERVER_ICONS, "dserver",
                       "Toggles object icons on server.",
                       f"Turns on/off server side object icons. No arguments.\n"
                       f"Reset mission to have server restart with this new setting."))
    prog_cmds.append(
        ProgramCommand(["ammo"], DSERVER_AMMO, "dserver",
                       "Toggles unlimited ammunition on server.",
                       f"Turns on/off unlimited ammunition on server. No arguments.\n"
                       f"Reset mission to have server restart with this new setting."))
    prog_cmds.append(
        ProgramCommand(["invuln"], DSERVER_INVULN, "dserver",
                       "Toggles plane/vehicle invulnerability on server.",
                       f"Turns on/off plane/vehicle invulnerability on server. No arguments.\n"
                       f"Reset mission to have server restart with this new setting."))
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
        Returns True/False and an index into the list of program commands """
    cmd_found = False
    i = -1
    for i, c in enumerate(p_cmds):
        if cmd_str in c.commands:
            cmd_found = True
            break
    return cmd_found, i


def process_user_commands(user_commands, r_con, mission, server_dict, prog_cmds,  help_str):
    """ Process pilot inputted commands queue """
    for command in user_commands:
        # flush any remaining commands after reset initiated
        if mission.load_new_mission_flag or mission.user_initiated_reset:
            print("reset ordered--breaking command processing")
            break

        # separate command and any following arguments into (only) two strings: command (one word) and arguments (1 or more words)
        cmd = command.split(' ', 1)
        cmd_word = cmd[0]
        if len(cmd) > 1:
            cmd_arguments = cmd[1]
        else:
            cmd_arguments = ''

        # determine if cmd_word is recognized
        found, index = is_cmd_in_program_commands(cmd_word, prog_cmds)

        if not found:
            r_con.send_msg(f"'{cmd_word}' is not a recognized recognized.", prefix='Syntax Error: ')
            print(f"Error: '{cmd_word}' is not a recognized recognized.")
            return

        cmd_type = prog_cmds[index].command_type  # shorthand var for command type like environmental, procedural, etc.
        print(f"Player command of '{cmd_word}' with arguments of '{cmd_arguments}'")

        """Process commands depending on type (e.g., help, environmental, etc. """
        if cmd_type == "help":
            if cmd_arguments:  # user has requested to print help for one or more commands
                print_help_for_individual_cmds(r_con, prog_cmds, cmd_arguments)
            else:  # otherwise print entire help message
                r_con.send_msg(help_str, prefix='')

        elif cmd_type == "environmental" and not mission.arcade_game:
            print("env cmd_arguments: ", cmd_arguments)
            flag = prog_cmds[index].cmd_method(cmd_arguments)  # all mis.env. methods accept a single string
            """ Append terminal message to remind user to reset mission to affect environmental changes """
            if mission.env.mission_environment_updated and flag:
                mission.env.console_msg += " Reset mission to put environmental changes into effect."
            r_con.send_msg(mission.env.console_msg)
            #  if environmental changes have made then resaver.exe needs to run later on mission reset
            mission.run_resaver = mission.env.mission_environment_updated  # an environment file change requires resaver
            print(f"environmental command message:", mission.env.console_msg)

        elif cmd_type == "procedural":
            prog_cmds[index].cmd_method(cmd_arguments)
            r_con.send_msg(mission.console_msg)  # print to console the resulting msg
            print(mission.console_msg)

        # server command -- send straight to dserver
        elif cmd_type == "server_command" and not mission.arcade_game:
            if cmd_arguments:  # user has requested to print help for one or more commands
                r_con.send_msg(f"Sending to server mission the input command '{cmd_arguments}'.")
                r_con.send(f"serverinput {cmd_arguments}")
            else:  # otherwise print entire help message
                r_con.send_msg(f"Error: {cmd_word} requires an argument.")  # print to console the resulting msg

        # dserver setting handling -- print server vars or toggle server value
        elif cmd_type == "dserver":
            if prog_cmds[index].cmd_method == PRINT_DSERVER_VARS:  # print server side variables
                pstr = f"Server side variables:\n"
                for s in server_dict.values():
                    pstr += s.print()
                r_con.send_msg(pstr)
            elif not mission.arcade_game:
                s = server_dict[prog_cmds[index].cmd_method]
                s.toggle_bool()
                r_con.send_msg(s.toggle_print())
                mission.restart_dserver = check_if_server_vars_updated(server_dict)  # true if just one of the server updated var is True

        elif mission.arcade_game and (cmd_type == "dserver" or cmd_type == "environmental" or cmd_type == "server_command"):
            r_con.send_msg("Environmental or server variable commands are not allowed during arcade play.")
            print("Environmental or server variable commands are not allowed during arcade play.")

        else:
            print("Error: I should never have gotten here during the processing of commands in 'program_commands.py'.")
            exit(-1)

    """
        Process three different types of mission resets (load_new mission, resaver.exe run, simple user initiated reset).
        Only send reset to mission running in Dserver if Dserver reboot is not required.
    """
    if mission.load_new_mission_flag:  # 1 -- note this will ignore/forget any environmental variables that were previously commanded
        mission.load_new_mission()
        if mission.arcade_game:  # check to see if dserver settings are set correctly for arcade game
            mission.restart_dserver = check_arcade_dserver_setting(server_dict)
        if not mission.restart_dserver:
            r_con.send_msg("Loading new scenario and resetting....")
            mission.reset_mission(r_con)
            mission.load_new_mission_flag = False
        mission.run_resaver = mission.env.mission_environment_updated = False  # ignore any of these commands set by player

    elif mission.run_resaver and mission.user_initiated_reset:  # 2
        # save mission and briefing string data to their respective files for resaver.exe processing
        mission.env.write_mission_file(mission.mission_filename)
        mission.env.write_briefing_file(mission.briefing_filename)

        mission.resaver(r_con)
        mission.run_resaver = mission.env.mission_environment_updated = False

        if not mission.restart_dserver:
            mission.reset_mission(r_con)
            mission.user_initiated_reset = False

    elif mission.user_initiated_reset:  # 3
        if not mission.restart_dserver:
            r_con.send_msg("Resetting mission....")
            mission.reset_mission(r_con)
            mission.init_mission_arcade()
            mission.user_initiated_reset = False
