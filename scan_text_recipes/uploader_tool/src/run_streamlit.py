import sys
import subprocess


python_executable = sys.executable

command = [python_executable, "-m", "streamlit", "run", "uploader.py"]

subprocess.run(command)
