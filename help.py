"""
    Functions associated with displaying help information for Il-2 multiplayer console display.
"""


def formatted_command_string(cmd_list):
    """ returns a nicely formatted string of all the commands associated with the list of commands """
    tmp_str = f"{':' * 20}  "
    for i in cmd_list[:-1]:
        tmp_str += f"{i}, "
    tmp_str += f"{cmd_list[-1]}"
    return tmp_str + f"  {':' * 20}\n"


def get_help_message(p_cmds):
    """ returns help message string for all user commands """
    dash_width = 45  # number of dashes to print out in a row
    dash_spaces = 0  # variable used to hack around the console antispam function which forbids repeated strings

    print_cmd_str = ""

    def print_dashes():
        """ helper function to print character width times followed by a space ns times
            By adding a space we get around the antispam mechanism """

        # I use a non standard utf-8 space character to get around il-2 console's antispam feature which forbids
        # repeated strings
        space_char = '\u00A0'
        nonlocal dash_spaces

        dash_spaces += 1
        return f"{'-' * dash_width + space_char * dash_spaces}\n"

    print_cmd_str += print_dashes()
    print_cmd_str = f"           SCG Training Server Commands \n"
    print_cmd_str += print_dashes()

    for c in p_cmds:
        print_cmd_str += formatted_command_string(c.commands)
        tmp_str = c.help_message.split('\n')
        for t in tmp_str:
            print_cmd_str += t + "\n"
    print_dashes()
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
            rc.send_msg(f"System error: Unable print help message for unrecognized command of '{c}'.")
