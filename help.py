from constants import FAKE_PREFIX

"""
    Functions associated with displaying help information for Il-2 multiplayer console display.
"""


def formatted_command_string(cmd_list):
    """ returns a nicely formatted string of all the commands associated with the list of commands """
    sep_char = '-'  # separator char
    num_seps = 6  # number of separators to print

    tmp_str = f"{sep_char * num_seps}  "
    tmp_str += cmd_list[0] + ' (aliases: '
    for i in cmd_list[1:-1]:
        tmp_str += f"{i}, "
    tmp_str += f"{cmd_list[-1]}"
    return tmp_str + f")  {sep_char * num_seps}\n"


def get_help_message(p_cmds):
    """ returns help message string for all user commands """
    dash_width = 28  # number of dashes to print out in a row
    dash_spaces = 0  # variable used to hack around the console antispam function which forbids repeated strings


    # ---------
    def print_dashes():
        """ helper function to print character width times followed by a space ns times
            By adding a space we get around the antispam mechanism """

        # I use a non-standard utf-8 space character to get around il-2 console's antispam feature which forbids
        # repeated strings
        space_char = '\u00A0'
        nonlocal dash_spaces

        dash_spaces += 1
        return f"{'-' * dash_width + space_char * dash_spaces}\n"
    # ---------

    print_cmd_str = print_dashes()
    print_cmd_str += f"SCG Training Server Commands \n"
    print_cmd_str += f"Type{FAKE_PREFIX}help (or{FAKE_PREFIX}h) followed by command listed below for more information.\n"
    print_cmd_str += f"For example:{FAKE_PREFIX}help winds\nNote that most commands can be called with shorter aliases.\n"
    print_cmd_str += "----\n"

    for c in p_cmds[1:]:  # skip the first command which should be the help command
        print_cmd_str += c.commands[0] + ' -- ' + c.short_help_str +   '\n'
        # print_cmd_str += formatted_command_string(c.commands)
        # tmp_str = c.help_message.split('\n')
        # for t in tmp_str:
            # print_cmd_str += t + "\n"

    # for c in p_cmds:
    #     print_cmd_str += formatted_command_string(c.commands)
    #     tmp_str = c.help_message.split('\n')
    #     for t in tmp_str:
    #         print_cmd_str += t + "\n"
    print_cmd_str += print_dashes()
    return print_cmd_str


def print_help_for_individual_cmds(rc, program_commands, commands_str):
    """ Takes a string of commands and sends to console"""
    from program_commands import is_cmd_in_program_commands
    cmd_list = commands_str.split(' ')
    for c in cmd_list:
        is_found, i = is_cmd_in_program_commands(c, program_commands)
        if is_found:
            rc.send_msg(formatted_command_string(program_commands[i].commands))
            rc.send_msg(program_commands[i].help_message)
        else:
            rc.send_msg(f"Error: '{c}' is an unrecognized command.")
