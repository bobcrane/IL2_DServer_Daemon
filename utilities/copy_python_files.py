import glob
import shutil
import time

sourcefiles = r"J:\PycharmProjects\il2server_script\*.py"
destdir = r"\\JUNEKIN\il2\data\Multiplayer\Dogfight\scg multiplayer server\python"
""" copy py files til Junekin"""
filenames = glob.glob(sourcefiles)
for f in filenames:
    x = shutil.copy(f, destdir)
    print(f"{f} -> {x}")

current_time = time.strftime("%H:%M:%S")
print("Copied at time:", current_time)