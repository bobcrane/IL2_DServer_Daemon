"""
    Functions associated help menu system.
"""

from constants import FAKE_PREFIX

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


def contruct_help_message(p_cmds):
    """ returns help message string for all user commands """
    dash_width = 28  # number of dashes to print out in a row
    dash_spaces = 0  # variable used to hack around the console antispam function which forbids repeated strings
    # dictionary of commands types defined in program_commands.py-- make sure they correspond
    command_types_dict = {"procedural": "Mission commands", "dserver": "Server side commands",
                          "server_command": '',
                          "environmental": "Environmental commands"}  # not counting help command type

    def print_dashes():
        """ helper function to print character width times followed by a space ns times
            By adding a space we get around the antispam mechanism """

        # I use a non-standard utf-8 space character to get around il-2 console's antispam feature which forbids
        # repeated strings
        space_char = '\u00A0'
        nonlocal dash_spaces

        dash_spaces += 1
        return f"{'-' * dash_width + space_char * dash_spaces}\n"

    # print_cmd_str = print_dashes()
    print_cmd_str = ''
    print_cmd_str += f"SCG Training Server Commands \n"
    print_cmd_str += print_dashes()
    print_cmd_str += f"Type{FAKE_PREFIX}help (or{FAKE_PREFIX}h) followed by a command for more detailed information.\n"
    print_cmd_str += f"For example:{FAKE_PREFIX}help winds\nNote that most commands can be called with shorter aliases.\n"


    cmd_type_set = set()  # will be used to create a header for the commands of that type that follow
    for c in p_cmds[1:]:  # skip the first command which should be the help command
        if c.command_type not in cmd_type_set:  # print only on first occurrence
            if command_types_dict[c.command_type]:
                print_cmd_str += f"\n----- {command_types_dict[c.command_type]} -----\n"
            cmd_type_set.add(c.command_type)
        print_cmd_str += c.commands[0] + ' -- ' + c.short_help_str + '\n'
    print_cmd_str += print_dashes()
    return print_cmd_str


def print_help_for_individual_cmds(rc, program_commands, commands_str):
    """ Takes a string of commands and sends to console"""
    from program_commands import is_cmd_in_program_commands
    cmd_list = commands_str.split(' ')
    for c in cmd_list:
        is_found, i = is_cmd_in_program_commands(c, program_commands)
        if is_found:
            # rc.send_msg(formatted_command_string(program_commands[i].commands), prefix='')
            # rc.send_msg(program_commands[i].help_message, prefix='')
            rc.send_msg(formatted_command_string(program_commands[i].commands) + program_commands[i].help_message, prefix='')
        else:
            rc.send_msg(f"'{c}' is an unrecognized command.", prefix='System Error: ')
