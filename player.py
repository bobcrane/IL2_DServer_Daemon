import time
import re
import pickle

""" player class and database functions """


class Player:
    """ Contains a pilots current alias, past aliasess, official player ID, and official alias ID """
    def __init__(self, player_name, rc):
        self.name = player_name  # current pilot handle
        self.aliases = [player_name]  # previous handles associated with this pilot
        time.sleep(1)
        rc.send("getplayerlist")  # determine if player is actually logged into DServe at this moment
        if player_name not in rc.response_string:  # player is not actually logged in
            print(f"server response in Player creation: {rc.response_string}")
            raise ValueError(f"Player initialization: {player_name} not reported in 'getplayerlist' call.")

        regexp = r"(?<=" + player_name + r",)\w+-\w+-\w+-\w+-\w+,\w+-\w+-\w+-\w+-\w+"
        match = re.search(regexp, rc.response_string)
        match1 = match.group()
        ids = match1.split(',')
        if len(ids) != 2:
            print(f"Error decoding player and profile IDs after console command 'getplayerlist': {ids}")
            exit(-1)
        else:
            self.player_id = ids[0]  # unique player ID assigned by IL-2 company
            self.profile_id = ids[1]  # unique profile ID assigned by IL-2 company


def update_player_list(_player, _player_list):
    """ updates the player_list; returns True if player_list file needs to be written later """
    for p in _player_list:
        if _player.player_id == p.player_id:
            if _player.name == p.name:
                return False  # no update needed
            else:
                if _player.name in p.aliases:  # alias found but update player_name to current one
                    p.name = _player.name
                    return True
                else:
                    p.aliases.append(_player.name)  # update the aliases to include current name
                    return True
    _player_list.append(_player)  # pilot not found so append player_list
    return True


def print_player_list(_player_list):
    for p in _player_list:
        alias_str = ''
        for i in p.aliases:
            alias_str += i + ' '
        print(f"{p.name:25} {alias_str:35} player_ID: {p.player_id}, profile_ID:, {p.profile_id}")


def read_player_list(_filename):
    with open(_filename, 'rb') as f:
        return pickle.load(f)


def write_player_list(_player_list, _filename):
    with open(_filename, 'wb') as f:
        pickle.dump(_player_list, f)

if __name__ == "__main__":
    from constants import IL2_PLAYER_LIST_FILE
    p = read_player_list(IL2_PLAYER_LIST_FILE)
    print_player_list(p)
