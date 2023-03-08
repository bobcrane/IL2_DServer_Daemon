"""
    Arcade game high scores database management and arcade game scoring classes and methods
    Note: Functions can be run as standalone commands from main()
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

    def print(self, detailed_scoring=True):
        print(f"{self.alias} ({self.player_id}),"
              f" plane={self.plane}, score={self.score},"
              # f"\ndetail_score={self.detailed_scoring},"
              f" date={self.timedate}")
        if detailed_scoring:
            print(self.detailed_scoring, '\n')


def read_scores(file=SCORES_DB):
    """ read high scores from file using pickle format """
    with open(file, 'rb') as f1:
        scores1 = pickle.load(f1)
    return scores1


def write_scores(scores, file=SCORES_DB):
    """ write high scores to file using pickle format """
    with open(file, 'wb') as f:
        pickle.dump(scores, f)


def print_scores(scores, detailed_scoring=False):
    if not scores:
        print("No scores present.")
        return

    for i, s in enumerate(scores):
        print(f"{i:>2}:", end='')
        s.print(detailed_scoring)


def get_high_scores(scores, num=5, f=lambda s: s.score, reverse_input=True):
    """ Return ordered list of high scores of length num using sort key f -- defaults to highest scores """
    high_scores = sorted(scores, key=f, reverse=reverse_input)
    if num > len(scores):
        num = len(scores)
    return high_scores[:num]


def get_plane_scores(scores, planetype, minimum=-10000):
    """ Return list of scores of only 'planetype' string (e.g., 'Ju-97 D-3', 'Bf-110 G-2', etc.) and larger than minimum """
    return [s for s in scores if s.plane == planetype and s.score > minimum]

def get_unique_scores(scores_, num_scores, sortkey='timedate'):
    """ Return list of unique player scores based on the sortkey attribute (e.g., 'timedate' or 'score') """
    sorted_scores = sorted(scores_, key=lambda s1: getattr(s1, sortkey), reverse=True)

    if num_scores > len(sorted_scores):
        num_scores = len(sorted_scores)
    unique_scores = []
    names = []
    num = 0
    for s in sorted_scores:
        if s.alias in names:
            continue
        else:
            names.append(s.alias)
            unique_scores.append(s)
            num += 1

        if num >= num_scores:
            break
    return unique_scores

def remove_last_score(file=SCORES_DB):
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


def enter_score(score, msg_str, arcadeplayer, db_file=SCORES_DB):
    """ Creates a GameResult object and stores it in the Pickle database file"""

    # captured only the detailed scoring information for mouse roll over on html high scores page
    web_msg = re.search(r'(?<=---\n)[\s\S]+(?=\n---*?)', msg_str).group()

    game_result = GameResult(arcadeplayer.alias, arcadeplayer.il2_player_id, arcadeplayer.plane_type, score, web_msg)

    try:
        high_scores = read_scores(file=db_file)
    except FileNotFoundError:
        high_scores = []

    if high_scores:
        high_scores = update_player_aliases(game_result, high_scores)

    high_scores.append(game_result)
    write_scores(high_scores, file=db_file)


def compute_score(player, vehicles):
    """
        Computer player score for last arcade game.  Returns integer score and string with detailed scoring information
    """
    if player.alias[-1] == 's':
        message = f"{player.alias}' scores "
    else:
        message = f"{player.alias}'s scores "
    message += f"for STUKA ATTACK! flying a {player.plane_type}\n"
    message += f"{'-'*3}\n"

    score = 0
    kill_str = ""
    damage_str = ""
    flush_width = 26
    # compute scores for vehicles destroyed and damaged
    for v in vehicles:
        if v.destroyed and v.player_damaged:
            kill_score = v.score * points['score_multi']
            score += kill_score
            # kill_str += f"{v.full_name:>32}: {kill_score:>6.0f} points\n"
            name_str = f"{v.full_name} (#{v.count_id:0>2}):"
            kill_str += f"{name_str:>{flush_width}} {kill_score} points\n"
        elif v.damage > 0.0:
            dmg_score = round(v.damage * v.score * points['dmg_mult']) * points['score_multi']
            score += dmg_score
            # damage_str += f"{v.full_name:>26} ({v.damage * 100:>02.0f}%): {dmg_score:>6.0f} points\n"
            tmp_str = f"{v.full_name} (#{v.count_id:0>2}) {v.damage * 100:>02.0f}%:"
            damage_str += f"{tmp_str:>{flush_width}} {dmg_score} points\n"

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
        pscore_str += f"{f'Pilot died:':>{flush_width-1}} {player_dmg} points\n"

    if player.ejected and not player.killed:
        eject_dmg = points['player_eject'] * points['score_multi']
        score += eject_dmg
        # pscore_str += f"{'Pilot ejected:':>33} {eject_dmg:>6} points\n"
        pscore_str += f"{f'Pilot ejected:':>{flush_width-1}} {eject_dmg} points\n"

    if player.damaged > 0.0 and not player.killed:
        player_dmg = round(player.damaged * points['player_dead'] * points['dmg_mult']) * points['score_multi']
        score += player_dmg
        # pscore_str += f"{'Pilot injured':>26} ({player.damaged * 100:>2.0f}%): {player_dmg:>6.0f} points\n"
        pscore_str += f"{'Pilot injured:':>{flush_width-1}} ({player.damaged * 100:>2.0f}%): {player_dmg} points\n"

    if player.plane_destroyed:
        plane_dmg = points['plane_destroyed'] * points['score_multi']
        # pscore_str += f"{player.plane_type + ' destroyed:':>33} {plane_dmg:>6.0f} points\n"
        pscore_str += f"{player.plane_type + ' destroyed:':>{flush_width-1}} {plane_dmg} points\n"
        score += plane_dmg
    elif player.plane_damaged:
        plane_dmg = round(player.plane_damaged * points['plane_destroyed'] * points['dmg_mult']) * points['score_multi']
        # pscore_str += f"{player.plane_type:>26} ({player.plane_damaged * 100:>02.0f}%): {plane_dmg:>6.0f} points\n"
        tmp_str = f"{player.plane_type} {player.plane_damaged * 100:>.0f}%:"
        pscore_str +=  f"{tmp_str:>{flush_width-1}} {plane_dmg} points\n"
        score += plane_dmg

    message += pscore_str
    message += f"{'-'*3}\n"
    # message += f"{'TOTAL SCORE:':>33} {score:>6.0f} points\n"
    message += f"{f'TOTAL SCORE:':>{flush_width-1}} {score:} points\n"

    return score, message


def html_write_scores(db_file=SCORES_DB, html_file=HTML_FILE, unique=False):
    """ Writes html high scores tables and upload to Neocities website """

    # create multiple indentation levels of 'indent_width'
    indent_width = 4
    ind = [' ' * x * indent_width for x in range(10)]

    """ 
        helper functions
        ----------------
    """
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
        return f"{ind[2]}<table>\n{ind[3]}<tr><th></th><th>Name</th><th>Score</th><th>Date</th></tr>\n"
        #  return f"{ind[2]}<table>\n{ind[3]}<tr><th></th><th>Name</th><th>Plane</th><th>Score</th><th>Date</th></tr>\n"


    # def table(sc, num_str):
    #     return f"{ind[3]}<tr><td>{num_str}</td><td>{sc.alias}</td><td>{sc.plane}</td>\n{ind[4]}" \
    #            f"<td>\n{ind[5]}<div class=\"tooltip\">{sc.score}" \
    #            f"\n{popup_tooltip(sc.detailed_scoring)}{ind[4]}</td>\n" \
    #            f"{ind[4]}<td>{sc.date_str}</td></tr>\n"

    def table(sc, num_str):
        return f"{ind[3]}<tr><td>{num_str}</td><td>{sc.alias}</td>\n{ind[4]}" \
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
    """ 
        - End helper funcs
    """

    # Read HTML file
    with open(html_file, 'r') as f:
        html_str = f.read()

    scores = read_scores(file=db_file)

    """
        TABLE #0:  Construct scores of last unique individual players
    """
    last_scores = get_unique_scores(scores, NUM_LAST_PLAYERS, sortkey='timedate')
    last_players_table = write_scores_table(last_scores, False)  # note that last player list is unnumbered
    html_str = re.sub(r'(?<=id="table0">\n)[\s\S]+?(?=    </div> <!--table0-->)', last_players_table, html_str)

    """"
        TABLE #1, #2, #3....-- Construct top scores for each individual plane (may only be 1 plane depending on game)
    """
    for i, p in enumerate(arcade_planes):  # currently only 1 plane; had multiple planes in the past but want to retain multi-plane functionality for the future
        plane_scores = get_plane_scores(scores, p, minimum=1)  # get score list of planes of type p only
        if unique:
            plane_high_scores = get_unique_scores(plane_scores, NUM_HIGH_SCORES, sortkey='score')
        else:
            plane_high_scores = get_high_scores(plane_scores, NUM_HIGH_SCORES)
        print_scores(plane_high_scores)
        plane_table = write_scores_table(plane_high_scores, True)
        regexp_str = f'(?<=id="table{i+1}">\\n)[\\s\\S]+?(?=    </div> <!--table{i+1}-->)'
        html_str = re.sub(regexp_str, plane_table, html_str)

    # write HTML file
    with open(html_file, 'w') as f:
        f.write(html_str)

    " upload HTML file to Neocities"
    uploaded, msg = upload_html_to_web(html_file, 'index.html')  # upload to internet
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


""" Run individual or custom scoring functions and db manipulation here """
def main():
    db_file = r'\\JUNEKIN\il2\data\Multiplayer\Dogfight\scg multiplayer server\high scores\highscores.pickle'
    htmlfile = r'\\JUNEKIN\il2\data\Multiplayer\Dogfight\scg multiplayer server\high scores\index.html'

    html_write_scores(db_file=db_file, html_file=htmlfile, unique=True)

    # scores = read_scores(file=db_file)
    # print_scores(scores, detailed_scoring=False)
    # # scores1 = scores.pop()
    # # print_scores([scores1], detailed_scoring=False)
    # del scores[9]
    # print_scores(scores, detailed_scoring=False)
    # write_scores(scores, file=db_file)


    # print(len(scores))
    # planestr = 'Bf 110 G-2'
    #
    # x = []
    # for s in scores:
    #     if planestr != s.plane:
    #         x.append(s)
    # scores = x
    #print_scores(scores)
    # write_scores(scores, file=db_file)





    # pass
    # remove_last_score()
    # html_write_scores()
    # scores = read_scores()
    #top_scores = get_high_scores(scores, 5)
    #print_scores(top_scores)

    # scores = read_scores(file=db_file)
    # for s in scores:
    #     if s.plane == 'Hs 129 B-2':
    #         print(s.plane)
    # print_scores(scores)

    # write_scores(scores, file=db_file)
    # for s in scores:
    #     s.detailed_scoring = re.sub(r'\(0', r'(', s.detailed_scoring)
    #     print(s.detailed_scoring)
    # write_scores(scores)
    # html_write_scores()
    #print_scores(scores, True)
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



if __name__ == "__main__":
    main()
