import sys
import subprocess


python_executable = sys.executable

command = [python_executable, "-m", "streamlit", "run", "streamlit_data_loader.py"]

subprocess.run(command)