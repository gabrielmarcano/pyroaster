import os
from pathlib import Path
import shutil
import subprocess
import mpy_cross

# Cleanup
if "out" in os.listdir():
    shutil.rmtree("out")

# Copy dirs
[shutil.copytree(dir, "out/" + dir) for dir in ["microdot", "lib", "drivers"]]

# Copy root py files
[
    shutil.copy(file.name, "out/" + file.name)
    for file in Path(".").glob("*.py")
    if not file.name.endswith(".template.py") and file.name != "build.py"
]

# Compile only py files in dirs
for py in Path("out").rglob("*/*.py"):
    mpy_cross.run(py.resolve())

# Delete py files
while True:
    mpy = [f for f in Path("out").rglob("*/*.mpy")]
    py = [f for f in Path("out").rglob("*/*.py")]
    if len(mpy) == len(py):
        [Path.unlink(f) for f in py]
        break


# Upload files

response = input("Upload files? (y/n) ")
if response == "y":
    commands = ["mpremote", "fs", "cp"]

    py_files = [f"{file.name}" for file in Path("out").glob("*.py")]
    subprocess.call(commands + py_files + [":"])

    mpy_dirs = [f"{dir}" for dir in Path("out").iterdir() if dir.is_dir()]
    subprocess.call(commands + ["-r"] + mpy_dirs + [":"])
