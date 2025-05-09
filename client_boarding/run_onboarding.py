import sys
import subprocess
import os

python_executable = sys.executable

# Make sure the path is correct relative to the Docker WORKDIR
script_path = os.path.join(os.path.dirname(__file__), "main.py")

command = [python_executable, "-m", "streamlit", "run", script_path]

subprocess.run(command)
