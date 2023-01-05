""""Environmental weather classes associated with IL-2 Mission files  """
import re
from collections import namedtuple
import glob


class WindLayer:
    """Class to hold and process IL-2 mission file wind layer data associated with altitude, speed, and direction"""
    def __init__(self, altitude):
        self.min_speed, self.max_speed = 0, 50  # min/max wind speed in m/s
        self.altitude = altitude
        self.speed = None
        self.true_direction = None
        self.rep_direction = None  # 'rep' = reciprocal
        self.console_msg = ""  # message to be sent to the il-2 console later

    def update_speed(self, speed):
        if (speed < self.min_speed or speed > self.max_speed) or not isinstance(speed, int):
            self.console_msg = f"Wind speed of '{speed}' is not between {self.min_speed} and {self.max_speed} m/s."
            return False
        self.speed = speed
        return True

    def update_direction(self, direction):
        if (direction < 0 or direction > 359) or not isinstance(direction, int):
            self.console_msg = f"Wind direction of '{direction}' is not a heading between 0° and 359°."
            return False

        self.true_direction = direction  # heading to write in user mission file for humans to read

        #  convert wind direction to its reciprocal since Il-2 stores wind speeds backwards
        #  (i.e., wind going to and not from)
        direction = direction - 180
        if direction < 0:
            direction += 360
        self.rep_direction = direction
        return True


class MissionEnvironment:
    """Class to hold all methods and variables that can be changed in an IL-2 Mission and briefing file data"""

    def __init__(self, cloud_filenames):
        # self.temperature = None  # temperature in C; 15 C is standard
        self.min_temp, self.max_temp = -40, 40  # min/max temp in celsius (integer)

        # self.time = None  # mission time in 24 hour format
        self.min_time, self.max_time = 0, 23  # military time from 0 to 23 hours (integer)

        # self.pressure = None  # pressure in mmHg; 760 is standard
        self.min_pres, self.max_pres = 370, 810  # min/max pressure in mmHg (integer)

        # self.turbulence = None  # strength of turbulence in mission.  float between 0.0 m/s and 10.0 m/s
        self.min_turb, self.max_turb = 0.0, 10.0  # turbulence from 0 m/s to 10 m/s (integer)

        # self.haze = None  # amount of haze in mission which limits visibility to the horizon.
        self.min_haze, self.max_haze = 0, 100  # haze in mission (int percentage value but write to mission file as proportion)

        # Wind layer variables
        self.windalts = (0, 500, 1000, 2000, 5000)  # the five predefined wind layer altitudes in IL-2
        self.num_windalts = len(self.windalts)  # number of wind altitudes specified above (i.e., 5)
        self.windlayers = None  # contains the speed and direction of wind at altitudes specified in windalts

        self.altitudes_str = ""  # constructs a string representing of the windalts above for later output
        for w in self.windalts[:-1]:
            self.altitudes_str += str(w) + "m, "
        self.altitudes_str += "and " + str(self.windalts[-1]) + "m"

        # clouds variables
        # self.cloud_description = ""  # First line of cloud data file summarizing the cloud data
        # self.cloud_data = ""  # Second line until last line of cloud data file
        # immutable, class like data structure describing cloud description and associated il-2 file data
        self.Clouds = namedtuple("Clouds", ['description', 'data'])
        self.clouds = []  # list of clouds_tuple above
        self.num_clouds = -1
        self.get_cloud_data(cloud_filenames)

        #  IL-2 Mission and briefing files data
        self.mission_data = None  # contents of IL-2 Mission File
        self.briefing_data = None  # contents of the IL-2 Briefing file

        self.mission_files_updated = False  # indicates whether or not mission file was updated
        self.console_msg = None  # message to send to the il-2 after processing command (string)
        # end init of class var


    def open_mission_file(self, filename):
        """ Opens IL-2 text mission file and stores in mission_data """
        with open(filename, 'r', encoding="UTF-8") as file:
            self.mission_data = file.read()

    def write_mission_file(self, filename):
        """ writes mission data to filename """
        with open(filename, 'w', encoding="UTF-8") as file:
            file.write(self.mission_data)

    def open_briefing_file(self, filename):
        """ Opens IL-2 text briefing file and stores in briefing_data """
        with open(filename, 'r', encoding="utf16") as file:
            self.briefing_data = file.read()

    def write_briefing_file(self, filename):
        """ writes briefing data to filename """
        with open(filename, 'w', encoding="utf16") as file:
            file.write(self.briefing_data)

    def update_temperature(self, temperature_str):
        """ Updates temperature in mission file string """
        try:
            temperature = int(temperature_str)
        except ValueError:
            self.console_msg = f"Input of '{temperature_str}' is not a valid temperature.  Input only a single value" \
                               f" between {self.min_temp} and {self.max_temp} C."
            return False
        else:
            if (temperature < self.min_temp) or (temperature > self.max_temp):
                self.console_msg = f"Temperature value of {temperature} is not between ({self.min_temp} and" \
                                   f" {self.max_temp} C)."
                return False
            else:
                # self.temperature = temperature
                self.console_msg = f"Temperature will be set to {temperature} °C at sea level."
                self.mission_data = re.sub(r"(?<=Temperature = )-*\d+(?=;)", str(temperature), self.mission_data)
                self.briefing_data = re.sub(r"(?<=Temperature \(0m\):</b> )-*\d+(?= C)", str(temperature),
                                            self.briefing_data)
                self.mission_files_updated = True
                return True

    def update_time(self, time_str):
        """ Updates time in mission file string -- only accepts a single hour value for time  """
        print("got to update_time() with time_str = ", time_str)
        try:
            time = int(time_str)
        except ValueError:
            self.console_msg = f"The input of '{time_str}' is not a valid time. Input only a single integer value between" \
                               f" {self.min_time} and {self.max_time} hours (e.g., 12)."
            return False
        else:
            if time < self.min_time or time > self.max_time:
                self.console_msg = f"Inputted time of '{time}' is not between the hours of {self.min_time} and" \
                                   f" {self.max_time}."
                return False
            else:
                # self.time = time
                self.console_msg = f"Mission time will be set to {time}:00 hours."
                self.mission_data = re.sub(r"(?<=Time = )\d+(?=:)", str(time), self.mission_data)
                self.briefing_data = re.sub(r"(?<=Start [tT]ime:</b> )\d\d(?=\d\d hours)", f"{time:02}",
                                            self.briefing_data)
                self.mission_files_updated = True
                return True

    def update_turbulence(self, turbulence_str):
        """ Updates turbulence in mission file string """
        try:
            turbulence = float(turbulence_str)
        except ValueError:
            self.console_msg = f"Input of '{turbulence_str}' is not a valid turbulence speed. Input only a single" \
                               f" value between {self.min_turb} and {self.max_turb} m/s."
            return False
        else:
            if turbulence < self.min_turb or turbulence > self.max_turb:
                self.console_msg = f"Turbulence value of '{turbulence}' is not between {self.min_turb} and " \
                                   f"{self.max_turb} m/s."
                return False
            else:
                # self.turbulence = turbulence
                self.console_msg = f"Mission turbulence will be set to {turbulence} m/s."
                self.mission_data = re.sub(r"(?<=Turbulence = )\d+[.]*[\d+]*(?=;)", f"{turbulence:.1f}", self.mission_data)
                self.briefing_data = re.sub(r"(?<=Turbulence:</b> )\d+[.]*[\d+]*(?= m/s)", f"{turbulence:.1f}", self.briefing_data)
                self.mission_files_updated = True
                return True

    def update_pressure(self, pressure_str):
        """ Updates barometric pressure in mission file string """
        try:
            pressure = int(pressure_str)
        except ValueError:
            self.console_msg = f"Input of '{pressure_str}' is not a valid barometric pressure. Input only a single" \
                               f" value between {self.min_pres} and {self.max_pres} mmHg."
            return False
        if pressure < self.min_pres or pressure > self.max_pres:
            self.console_msg = f"Pressure value of '{pressure}' is not between {self.min_pres} and {self.max_pres}" \
                               f" mmHg.\n     Note that standard pressure is 760 mmHg at sea level."
            return False
        else:
            # self.pressure = pressure
            self.console_msg = f"Pressure will be set to {pressure} mmHg."
            self.mission_data = re.sub(r"(?<=Pressure = )-*\d+(?=;)", str(pressure), self.mission_data)
            self.briefing_data = re.sub(r"(?<=Pressure \(0m\):</b> )-*\d+(?= mmHg)", str(pressure), self.briefing_data)
            self.mission_files_updated = True
            return True

    def update_haze(self, haze_str):
        """ Updates haze in mission file string -- float value between 0.0 and 1.0 """
        try:
            haze = int(haze_str)
        except ValueError:
            self.console_msg = f"Haze value of '{haze_str}' is not a valid integer value between {self.min_haze}" \
                               f" and {self.max_haze}."
        else:
            if haze < self.min_haze or haze > self.max_haze:
                self.console_msg = f"Haze value of '{haze}' is not between {self.min_haze} and {self.max_haze}."
                return False
            else:
                self.haze = haze
                self.console_msg = f"Haze will be set to a value of {haze}%."
                haze_proportion = haze / 100.0
                self.mission_data = re.sub(r"(?<=Haze = )\d+[.]*[\d+]*(?=;)", f"{haze_proportion:.2f}", self.mission_data)
                self.briefing_data = re.sub(r"(?<=Haze:</b> )\d+(?=%)", str(haze), self.briefing_data)
                self.mission_files_updated = True
                return True

    def update_wind(self, winds_str):
        """ Updates wind layer data in mission file.  Expects between 1 and 5 wind layers using speed(m/s)@direction
            format (e.g., 10@230) """
        inputed_winds = winds_str.split()
        num_wind_args = len(inputed_winds)
        if num_wind_args < 1 or num_wind_args > self.num_windalts:
            self.console_msg = f"Wind layer input of '{winds_str}' is not between 1 and {self.num_windalts} wind" \
                               f" layers or is not valid. Enter between 1 and {self.num_windalts} wind layers using" \
                               f" speed@direction format (e.g.,'4@90')"
            return False

        """Updates up to five wind layers in mission file string """
        self.windlayers = []  # clear any previous windlayer data
        for w in self.windalts:   # create the wind layers list at the different altitudes.
            self.windlayers.append(WindLayer(w))

        # Parse inputted wind list (e.g, [3@350, 6@345, 10@330]) and create wind layers
        for i in range(0, num_wind_args):
            tmp_str = inputed_winds[i]
            try:
                ipos = tmp_str.index('@')
                speed = int(tmp_str[:ipos])
                direction = int(tmp_str[ipos + 1:])
            except ValueError:
                self.console_msg = f"Inputted value of '{tmp_str}' is not a valid wind layer.  Enter between 1" \
                                   f" and {self.num_windalts} layers of wind using speed@direction format (e.g., 4@90)." \
                                   f" Also note that there are no spaces around the @ character between the wind speed and direction."

                return False
            else:
                if not self.windlayers[i].update_speed(speed):
                    self.console_msg = self.windlayers[i].console_msg
                    return False  # incorrect value for speed
                if not self.windlayers[i].update_direction(direction):
                    self.console_msg = self.windlayers[i].console_msg
                    return False  # incorrect value for direction

        # if not all (5) wind altitudes specified then fill in the rest of layers with very last speed@dir value pair given
        for j in range(i + 1, self.num_windalts):
            self.windlayers[j].update_speed(speed)  # okay to ignore return value because direction and speed are previously validated
            self.windlayers[j].update_direction(direction)

        # create replacement string for wind layer data
        wind_replacement_str = "WindLayers\n  {\n"
        for w in self.windlayers:
            wind_replacement_str += f"     {w.altitude} :     {w.rep_direction}  :     {w.speed};\n"
        wind_replacement_str += "  }"
        # replace wind layer data using a regular expression search (text starting with 'Windlayers {' and ending with '}')
        self.mission_data = re.sub(r"WindLayers\s+{([^}]+)}", wind_replacement_str, self.mission_data)

        # replace wind layer data in briefing file
        for i in range(0, self.num_windalts):
            wind_replacement_str = f"  {self.windlayers[i].speed} m/s @ {self.windlayers[i].true_direction}"
            regexp = r"(?<= " + str(self.windalts[i]) + r"m</b>)\s+\d+ m/s @ \d+(?=°)"
            self.briefing_data = re.sub(regexp, wind_replacement_str, self.briefing_data)

        # Create validated console message
        self.console_msg = "Winds will be set to:\n"
        for w in self.windlayers:
            self.console_msg = self.console_msg + f" {w.altitude:6}m: {w.speed:2}m/s @ {w.true_direction:3}°\n"

        self.mission_files_updated = True
        return True

    def get_cloud_data(self, cloud_files_prefix):
        """Identify files with cloud data, load them, and store them in a list"""
        cloud_filenames = glob.glob(cloud_files_prefix)  # find all the cloud files defined by cloud_files_prefix
        self.clouds = []  # will be assigned a
        for filename in cloud_filenames:
            with open(filename, 'r') as file_object:
                file_str = file_object.read()
            split_str = file_str.split('\n', 1)
            # first element is description of the clouds and the second is the data
            self.clouds.append(self.Clouds(split_str[0], split_str[1]))
        self.num_clouds = len(self.clouds)

    def list_cloud_data(self, unused_arg):
        """ Lists the available cloud sets for IL-2 console print -- tmp_str argument is ignored """
        self.console_msg = 'The following cloud configurations are available:\n'
        for i, cloud in enumerate(self.clouds):
            self.console_msg += f"     {i:2}: {cloud.description}\n"
        self.console_msg += "\nUse the command 'set_clouds' followed by one of the numbers given above to set the clouds for the next mission (e.g., 'set_clouds 0')."
        return False

    def update_clouds(self, cloud_index_str):
        try:
            index = int(cloud_index_str)
        except ValueError:
            self.console_msg = f"Input of '{cloud_index_str}' is not a valid cloud configuration index.\n"\
                               f"Input only a single integer value between 0 and {self.num_clouds - 1}."
            return False
        if index < 0 or index > self.num_clouds - 1:
            self.console_msg = f"Cloud configuration index value of '{index}' is not between 0" \
                               f" and {self.num_clouds - 1}"
            return False
        else:
            self.console_msg = f"Clouds will be set to cloud configuration #{index}: {self.clouds[index].description}"
            # cloud data contains backslashes which must be escaped with an additional backslash for the regular
            #  expression substitute to work correctly below
            tmp_str = self.clouds[index].data.replace("\\", "\\\\")
            self.mission_data = re.sub(r"\s\sCloudLevel([\w\W]+)(?=\s\sTurb)", tmp_str, self.mission_data)
            self.briefing_data = re.sub(r"(?<=Clouds:</b> )(.*?)(?=<br)", self.clouds[index].description, self.briefing_data)

            self.mission_files_updated = True
            return True
