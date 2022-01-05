"""
    Arcade game high scores database management functions
    Note: Functions can be run as stand alone commands from main()
"""

import pickle
import re
from datetime import datetime
import neocities
import requests

from constants import points, SCORES_DB, HTML_FILE, arcade_planes, NUM_LAST_PLAYERS, NUM_HIGH_SCORES


class GameResult:
    def __init__(self, _name, player_id, _plane, _score, _scoring):
        self.alias = _name  # current alias of the player
        self.player_id = player_id  # official IL-2 assign user-id of player
        self.plane = _plane  # player plane description
        self.score = _score  # total score of game result
        self.detailed_scoring = _scoring  # string containing detailed scoring information
        self.timedate = datetime.now()  # timestamp used for sorting purposes
        self.date_str = self.timedate.strftime("%Y-%m-%d")  # date to display on high scores page

    def print(self):
        print(f"alias={self.alias}",
              # f" playerID={self.player_id},"
              f" plane={self.plane}, score={self.score},"
              # f"\ndetail_score={self.detailed_scoring},"
              f" date={self.timedate}")


def read_scores():
    """ read high scores from file using pickle format """
    with open(SCORES_DB, 'rb') as f1:
        scores1 = pickle.load(f1)
    return scores1


def write_scores(scores):
    """ write high scores to file using pickle format """
    with open(SCORES_DB, 'wb') as f:
        pickle.dump(scores, f)


def print_scores(scores):
    if not scores:
        print("No scores present.")
        return

    for i, s in enumerate(scores):
        print(f"{i:>2}:", end='')
        s.print()


def get_high_scores(scores, num=5, f=lambda s: s.score, reverse_input=True):
    """ Return ordered list of high scores of length num using sort key f -- defaults to highest scores """
    high_scores = sorted(scores, key=f, reverse=reverse_input)
    if num > len(scores):
        num = len(scores)
    return high_scores[:num]


def get_plane_scores(scores, planetype):
    """ Return list of scores of only 'planetype' string (e.g., 'Ju-97 D-3', 'Bf-110 G-2', etc.) """
    return [s for s in scores if s.plane == planetype]

def get_unique_last_players(scores_, num_last_plays):
    """ Return list of scores of the last UNIQUE individual players you played last """
    last_scores = sorted(scores_, key=lambda s1: s1.timedate, reverse=True)
    if num_last_plays > len(last_scores):
        num_last_plays = len(scores_)
    last_players = []
    name = []
    for i, s in enumerate(last_scores):
        if s.alias in name:
            continue
        else:
            name.append(s.alias)
            last_players.append(s)
        if i >= num_last_plays:
            break
    return last_players


def remove_last_score():
    _scores = read_scores()
    if not _scores:
        print("No arcade scores in database.")
        return
    _scores.pop()
    write_scores(_scores)


def update_player_aliases(last, game_results):
    """
        Replaces aliases of game_results with last game alias using official IL-2 pilot id string if needed.
        Prevents people from changing their in game alias and showing different names on the leaderboard when in fact
        it is the exact same person--it is impossible to spoof the pilot id.
    """

    for i in game_results:
        if last.player_id == i.player_id and last.alias != i.alias:
            i.alias = last.alias

    return game_results


def enter_score(score, msg_str, arcadeplayer):
    """ Creates a GameResult object and stores it in the Pickle database file"""

    # captured only the detailed scoring information for mouse roll over on html high scores page
    web_msg = re.search(r'(?<=---\n)[\s\S]+(?=\n---*?)', msg_str).group()

    game_result = GameResult(arcadeplayer.alias, arcadeplayer.il2_player_id, arcadeplayer.plane_type, score, web_msg)

    try:
        high_scores = read_scores()
    except FileNotFoundError:
        high_scores = []

    if high_scores:
        high_scores = update_player_aliases(game_result, high_scores)

    high_scores.append(game_result)
    write_scores(high_scores)


def compute_score(player, vehicles):
    if player.alias[-1] == 's':
        message = f"{player.alias}' scores "
    else:
        message = f"{player.alias}'s scores "
    message += 'for STUKA ATTACK!\n'
    message += f"{'-'*3}\n"

    score = 0
    kill_str = ""
    damage_str = ""
    # compute scores for vehicles destroyed and damaged
    for v in vehicles:
        if v.destroyed and v.player_damaged:
            kill_score = v.score * points['score_multi']
            score += kill_score
            # kill_str += f"{v.full_name:>32}: {kill_score:>6.0f} points\n"
            kill_str += f"{v.full_name}: {kill_score} points\n"
        elif v.damage > 0.0:
            dmg_score = round(v.damage * v.score * points['dmg_mult']) * points['score_multi']
            score += dmg_score
            # damage_str += f"{v.full_name:>26} ({v.damage * 100:>02.0f}%): {dmg_score:>6.0f} points\n"
            damage_str += f"{v.full_name} ({v.damage * 100:>02.0f}%): {dmg_score} points\n"

    if not kill_str and not damage_str:
        # message += f"{'No vehicles destroyed:':>33}{0:>7.0f} points\n"
        # message += f"{'No vehicles damaged:':>33}{0:>7.0f} points\n"
        message += f"No vehicles destroyed: 0 points\n"
        message += f"No vehicles damaged: 0 points\n"
    if kill_str:
        message += "Vehicles Killed:\n" + kill_str
    if damage_str:
        message += "Vehicles Damaged:\n" + damage_str

    # compute scores for player's character and plane being damaged/destroyed
    pscore_str = "Player Damage:\n"  # player penalty scoring string
    if player.killed:
        player_dmg = points['player_dead'] * points['score_multi']
        score += player_dmg
        # pscore_str += f"{'Pilot died:':>24} {player_dmg:>6} points\n"
        pscore_str += f"Pilot died: {player_dmg} points\n"

    if player.ejected and not player.killed:
        eject_dmg = points['player_eject'] * points['score_multi']
        score += eject_dmg
        # pscore_str += f"{'Pilot ejected:':>33} {eject_dmg:>6} points\n"
        pscore_str += f"Pilot ejected: {eject_dmg} points\n"

    if player.damaged > 0.0 and not player.killed:
        player_dmg = round(player.damaged * points['player_dead'] * points['dmg_mult']) * points['score_multi']
        score += player_dmg
        # pscore_str += f"{'Pilot injured':>26} ({player.damaged * 100:>2.0f}%): {player_dmg:>6.0f} points\n"
        pscore_str += f"Pilot injured: ({player.damaged * 100:>2.0f}%): {player_dmg} points\n"

    if player.plane_destroyed:
        plane_dmg = points['plane_destroyed'] * points['score_multi']
        # pscore_str += f"{player.plane_type + ' destroyed:':>33} {plane_dmg:>6.0f} points\n"
        pscore_str += f"{player.plane_type + ' destroyed:'} {plane_dmg} points\n"
        score += plane_dmg
    elif player.plane_damaged:
        plane_dmg = round(player.plane_damaged * points['plane_destroyed'] * points['dmg_mult']) * points['score_multi']
        # pscore_str += f"{player.plane_type:>26} ({player.plane_damaged * 100:>02.0f}%): {plane_dmg:>6.0f} points\n"
        pscore_str += f"{player.plane_type} ({player.plane_damaged * 100:>02.0f}%): {plane_dmg} points\n"

        score += plane_dmg

    message += pscore_str
    message += f"{'-'*3}\n"
    # message += f"{'TOTAL SCORE:':>33} {score:>6.0f} points\n"
    message += f"TOTAL SCORE: {score:} points\n"

    return score, message


def html_write_scores():
    """ Writes html high scores tables and upload to Neocities website """

    # create multiple indentation levels of 'indent_width'
    indent_width = 4
    ind = [' ' * x * indent_width for x in range(10)]

    """ helper functions """
    def popup_tooltip(detailed_scoring_str):
        """ Write html popup tooltip that contains detailed scoring information """
        first = True
        lines = detailed_scoring_str.split('\n')
        # print('lines:')
        # print(lines)
        html_txt = ind[6] + '<span class="tooltiptext">\n'
        html_txt += ind[7] + '<table  class="t1">\n'
        for l in lines:
            pos = l.index(':')
            left = l[0:pos].lstrip().rstrip()
            right = l[pos + 1:].lstrip().rstrip()
            if not right and first:  # row is a header type so insert a blank line beforehand if not first
                first = False
            elif not right:
                html_txt += ind[8] + '<tr><td>&nbsp</td><td>&nbsp</td></tr>\n'
            html_txt += ind[8] + '<tr>'
            html_txt += f"<td>{left}</td><td>{right}</td>"
            html_txt += '</tr>\n'

        html_txt += ind[7] + '</table>\n'
        html_txt += ind[6] + '</span>\n' + ind[5] + '</div>\n'
        return html_txt

    def header():
        return f"{ind[2]}<table>\n{ind[3]}<tr><th></th><th>Name</th><th>Plane</th><th>Score</th><th>Date</th></tr>\n"

    def table(sc, num_str):
        return f"{ind[3]}<tr><td>{num_str}</td><td>{sc.alias}</td><td>{sc.plane}</td>\n{ind[4]}" \
               f"<td>\n{ind[5]}<div class=\"tooltip\">{sc.score}" \
               f"\n{popup_tooltip(sc.detailed_scoring)}{ind[4]}</td>\n" \
               f"{ind[4]}<td>{sc.date_str}</td></tr>\n"

    def write_scores_table(scores_, numbered):
        """ Construct HTML table of list of scores_ """
        table_str = header()
        # num_scores = len(scores_)

        for i, s in enumerate(scores_):
            if numbered:
                num_str = f"#{i+1}"
            else:
                num_str = "&nbsp&nbsp&nbsp&nbsp"
            table_str += table(s, num_str)
        table_str += ind[2] + '</table>\n'
        return table_str
    """ end helper functions """

    # Read HTML file
    with open(HTML_FILE, 'r') as f:
        html_str = f.read()

    # html_write_scores main()
    scores = read_scores()

    """
        TABLE #0:  Construct scores of last unique individual players
    """
    last_scores = get_unique_last_players(scores, NUM_LAST_PLAYERS)
    last_players_table = write_scores_table(last_scores, False)  # note that last player list is unnumbered
    html_str = re.sub(r'(?<=id="table0">\n)[\s\S]+?(?=    </div> <!--table0-->)', last_players_table, html_str)

    """"
        TABLE #1, #2, #3....-- Construct top scores for each individual plane
    """
    for i, p in enumerate(arcade_planes):
        plane_scores = get_plane_scores(scores, p)  # get score list of planes of type p only
        plane_high_scores = get_high_scores(plane_scores, NUM_HIGH_SCORES)
        plane_table = write_scores_table(plane_high_scores, True)
        regexp_str = f'(?<=id="table{i+1}">\\n)[\\s\\S]+?(?=    </div> <!--table{i+1}-->)'
        html_str = re.sub(regexp_str, plane_table, html_str)

    # write HTML file
    with open(HTML_FILE, 'w') as f:
        f.write(html_str)

    " upload HTML file to Neocities"
    uploaded, msg = upload_html_to_web(HTML_FILE, 'index.html')  # upload to internet
    print(f"Neocities upload result: {msg}")


def upload_html_to_web(source, destination):
    """
        Uploads a local file to Neocities destination file.
        Neocites object is used to interact with the Neocities API for file upload
        Source: https://github.com/neocities/python-neocities
    """

    nc = neocities.NeoCities('il2arcade', 'arcade1!A')   # two args are login/password

    try:
        response = nc.upload((source, destination))

    except requests.exceptions.ConnectTimeout:
        return False, "Upload failure: Timeout error connecting to neocities.org."

    except nc.InvalidRequestError:
        return False, f"Upload failure: Failed to upload file '{source}' to neocities.org"

    return True, response['message']


def main():
    pass
    # remove_last_score()
    # html_write_scores()
    # scores = read_scores()
    # top_scores = get_high_scores(scores, 5)
    # print_scores(scores)

    # scores = read_scores()
    # last_scores = get_unique_last_players(scores, 5)
    # print(f"\n----Last players----")
    # print_scores(last_scores)

    # scores = read_scores()
    # for i, p in enumerate(arcade_planes):
    #     print(f"\n----{p} = {plane_nicknames[p]}----")
    #     plane_scores = get_plane_scores(scores, p)  # get score list of planes of type p only
    #     plane_high_scores = get_high_scores(plane_scores, NUM_HIGH_SCORES)
    #     print_scores(plane_high_scores)
        #plane_table = write_scores_table(plane_high_scores, True)



    # for p in arcade_planes:
    #     print(f"\n----{p} = {plane_nicknames[p]}----")
    #     p_scores = get_plane_scores(scores, p)
    #     high_scores = get_high_scores(p_scores, 5)
    #     # print(f"--- {plane_nicknames[p]} ---")
    #     print_scores(high_scores)


    # html_write_scores()
    # int_high_scores()
    # uploaded, msg = upload_html_to_web(HTML_FILE, 'index.html')
    # uploaded, msg = upload_html_to_web(CSS_FILE, 'style.css')


""" Run individual scoring functions here """
if __name__ == "__main__":
    main()
