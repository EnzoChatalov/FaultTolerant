import subprocess

num_processes = 5

for i in range(num_processes):
    # 'start cmd /k' opens a new Command Prompt window and keeps it open
    subprocess.Popen(f'start cmd /k "python main.py {i}"', shell=True)
