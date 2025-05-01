import sys
import subprocess


python_executable = sys.executable

command = [python_executable, "-m", "streamlit", "run", "main.py"]

subprocess.run(command)
