"""
 IL2 DServer program constants
 All program constansts are stored in this file with the exception of some additional ones in the Mission class.
"""

IL2_BASE_DIR = r'\\JUNEKIN\il2' + '\\'
IL2_MISSION_DIR = IL2_BASE_DIR + r'data\Multiplayer\Dogfight\scg multiplayer server' + '\\'
MISSION_BASENAME = 'scg_training'  # mission run solely by DServer.exe

# chat log files constants
CHATLOG_DIR = IL2_BASE_DIR + r'\data\logs\chat' + '\\'  # directory of Il-2 chat log files
CHATLOG_FILES_WILDCARD = CHATLOG_DIR + '*.chatlog'  # chat log wildcard selector
CHATLOG_DIR_BACKUP = CHATLOG_DIR + 'bak'

MY_LOG_FILE = IL2_MISSION_DIR + r'python\scg_pilot_log.txt'  # text file to store pilot connections and exits

CLOUD_FILES_WILDCARD = IL2_MISSION_DIR + r'clouds\*.txt'  # cloud data is stored in files clouds00.text, etc.
IL2_PLAYER_LIST_FILE = IL2_MISSION_DIR + r'python\player_list.pickle'  # permanently holds player IDs

# TCP/IP values of server and login credentials
DSERVER_IP = '192.168.0.99'
DSERVER_PORT = 8991
DSERVER_USERNAME = 'scg'
DSERVER_PASSWORD = 's1'

# log file booleans
COPY_MISSION_LOGFILES = True
KEEP_CHAT_LOGS = True  # whether or not to preserve the chat log files

# misc constants
SLEEP_TIME = 3  # amount of time for this script to sleep in between dumping chat log file and parsing that file
RESET_TIME = 2 * 60 * 60  # time in seconds to possibly reload the default mission after player inactivity; 2 hours
CMD_PREFIX = '$$'  # the escape character sequence indicating a user command has been entered (e.g., $$time 23)
# same as above but use to prevent parser from interpreting printed help messages as user commands causing loops
FAKE_PREFIX = '\u00A0$$'

# arcade game constants
MISSION_LOG_DIR = IL2_BASE_DIR + r'data\logs\mission' + '\\'
MISSION_LOGS_WILDCARD = MISSION_LOG_DIR + r'm*.txt'
MISSION_LOG_BACKUP_DIR = MISSION_LOG_DIR + r'bak'
HTML_DIR = IL2_MISSION_DIR + 'high scores' + '\\'
HTML_FILE = HTML_DIR + r'index.html'
CSS_FILE = HTML_DIR + r'style.css'
SCORES_DB = HTML_DIR + r'highscores.pickle'
MISSION_FILENAME = IL2_MISSION_DIR + r'current mission text files' + '\\' + MISSION_BASENAME + r'.mission'
MISSION_BRIEFING = IL2_MISSION_DIR + r'current mission text files' + '\\' + MISSION_BASENAME + r'.eng'

# arcade game constants
NUM_LAST_PLAYERS = 5  # number of scores to list for the last unique player table
NUM_HIGH_SCORES = 5  # number of high scores to show for the other high scores tables
arcade_planes = ('Ju 87 D-3', 'Hs 129 B-2', 'Bf 110 G-2')

plane_nicknames = {
    'Ju 87 D-3': 'Ju 87 D-3 Kanonenvogel',
    'Hs 129 B-2': 'Hs 129 B-2 Panzerknacker',
    'Bf 110 G-2': 'Bf 110 G-2 Kampfzerstorer'
}

points = {
    # score modifiers
    'score_multi': 10,  # multiply final scores by this amount
    'dmg_mult': .666667,  # score award multiplier for partial damage applied when target is not destroyed

    # player penalties
    'plane_destroyed': -1000,
    'player_eject': -300,
    'player_dead': -1500,

    # vehicle target scores:
    'kv1-42': 600,
    't34-76stz': 400,
    't34-76stz-41': 400,
    't34-76-43': 400,
    'bt7m': 200,
    'm3a1': 100
}

HIGHSCORES_URL = 'https://il2arcade.neocities.org'