"""
    IL2 DServer daemon program constants
    Important global constants are stored in this file.
    (Note: Some additional filename and extension constants are stored in the Mission class.)
"""

BASE_MISSION_NUM = 5  # index of the available missions used to load first and default mission --frequently changed so on top here

IL2_BASE_DIR = r'E:\il2' + '\\'  # where IL-2 files resides
# IL2_BASE_DIR = r'\\JUNEKIN\il2' + '\\'  # Note that network drive paths do not work well with some IL-2 executables like DServer.exe; this path provided here for code debugging.
IL2_MISSION_DIR = IL2_BASE_DIR + r'data\Multiplayer\Dogfight\scg multiplayer server' + '\\'
MISSION_BASENAME = 'scg_training'  # basename of the mission files that dserver loads and runs

# DServer.exe associated constants
IL2_DSERVER_DIR = IL2_BASE_DIR + r'bin\game' + '\\'
IL2_DSERVER_EXE = 'DServer.exe'
IL2_DSERVER_WORKING_CONFIG = IL2_DSERVER_DIR + 'scg_working.sds'
IL2_DSERVER_BASE_CONFIG = IL2_DSERVER_DIR + 'scg_base.sds'

# Dserver settings that can be toggled -- see program_commands.py
DSERVER_AIM = 'aim'
DSERVER_ICONS = 'icons'
DSERVER_AMMO = 'ammo'
DSERVER_INVULN = 'invuln'  # invulnerability
PRINT_DSERVER_VARS = 'dserver_vars'  # this is actual the print help flag and not an actual toggleable setting

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
COPY_MISSION_LOGFILES = True  # store mission log files in a backup directory?
KEEP_CHAT_LOGS = True  # whether to preserve the chat log files

# misc constants
SLEEP_TIME = 3  # amount of seconds for this script between each iteration (before dumping chatlog)
RESET_TIME = 2 * 60 * 60  # time in seconds to possibly reload the default mission after player inactivity; 2 hours
# RESET_TIME = 2 * 60  # debug reset time -- very short time
CMD_PREFIX = '$$'  # the command character sequence indicating a user command has been entered (e.g., $$time 23)
# same as above but use to prevent parser from interpreting printed help messages as user commands causing loops
FAKE_PREFIX = '\u00A0$$'  # a space character that (miraculously) defeats il-2 chat anti-spam detection


# arcade game constants
# Dserver settings required for arcade playing (i.e., no cheat settings)
STUKA_DSERVER_SETTINGS = {DSERVER_AMMO: False, DSERVER_ICONS: False, DSERVER_INVULN: False}
MISSION_LOG_DIR = IL2_BASE_DIR + r'data\logs\mission' + '\\'
MISSION_LOGS_WILDCARD = MISSION_LOG_DIR + r'm*.txt'
MISSION_LOG_BACKUP_DIR = MISSION_LOG_DIR + r'bak'
HTML_DIR = IL2_MISSION_DIR + 'high scores' + '\\'
HTML_FILE = HTML_DIR + r'index.html'
CSS_FILE = HTML_DIR + r'style.css'
SCORES_DB = HTML_DIR + r'highscores.pickle'
NUM_LAST_PLAYERS = 5  # number of scores to list for the last unique player table
NUM_HIGH_SCORES = 20  # number of high scores to show for the other high scores tables
arcade_planes = ['Ju 87 D-3']
AIR_SPAWNS = ['spawn2', 'spawn3', 'spawn4']  # air spawns which can be unlocked
# arcade_planes = ('Ju 87 D-3', 'Hs 129 B-2', 'Bf 110 G-2')

plane_nicknames = {
    'Ju 87 D-3': 'Ju 87 D-3 Kanonenvogel',
    'Hs 129 B-2': 'Hs 129 B-2 Panzerknacker',
    'Bf 110 G-2': 'Bf 110 G-2 Kampfzerstorer'
}

points = {
    # score modifiers
    'score_multi': 1,  # multiply final scores by this amount
    'dmg_mult': .5,  # score award multiplier for partial damage applied when target is not destroyed

    # player penalties
    'plane_destroyed': -500,
    'player_eject': -250,
    'player_dead': -500,

    # vehicle target scores:
    'kv1-42': 1000,
    't34-76stz': 500,
    't34-76stz-41': 500,
    't34-76-43': 500,
    'bt7m': 200,
    'm3a1': 100
}

SCORING_MILESTONES = [600, 1400, 2400]  # points need to unlock air spawn (i.e., new life)

HIGHSCORES_URL = 'https://il2arcade.neocities.org'
