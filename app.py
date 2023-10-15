import subprocess
import platform
import time
import urllib.request
import json
import sys
import tkinter as tk
from tkinter import ttk, filedialog
import os

def start_ngrok():
    global ngrok_process
    ngrok_process = subprocess.Popen(['ngrok', 'tcp', '25565'], shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(2)
    return ngrok_process

def get_ngrok_url():
    with urllib.request.urlopen("http://localhost:4040/api/tunnels") as response:
        data = response.read()
    datajson = json.loads(data)
    ngrok_urls = [tunnel['public_url'] for tunnel in datajson['tunnels']]
    ngrok_urls = [url.replace("tcp://", "") for url in ngrok_urls]
    return ngrok_urls

def copy(txt):
    if platform.system() == "Windows":
        cmd = 'echo ' + txt.strip() + ' | clip'
    if platform.system() == "Darwin":
        cmd = 'echo ' + txt.strip() + ' | pbcopy'
    if platform.system() == "Linux":
        cmd = 'echo ' + txt.strip() + ' | xclip'
    return subprocess.check_call(cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def start_server(jar_file, ram):
    print("Starting ngrok...")
    ngrok_process = start_ngrok()

    ngrok_urls = get_ngrok_url()
    copy(ngrok_urls[0])
    print("Copied ngrok URL \"" + ngrok_urls[0] + "\" to Clipboard")

    print("Starting Minecraft Server...")
    
    server_directory = os.path.dirname(jar_file)
    
    minecraft_process = subprocess.Popen(['java', '-XX:+UseG1GC', f'-Xmx{ram}G', f'-Xms{ram}G', '-Dsun.rmi.dgc.server.gcInterval=2147483646', '-XX:+UnlockExperimentalVMOptions', '-XX:G1NewSizePercent=20', '-XX:G1ReservePercent=20', '-XX:MaxGCPauseMillis=50', '-XX:G1HeapRegionSize=32M', '-jar', jar_file, 'nogui'], cwd=server_directory)

    minecraft_process.wait()
    print("Server Exited")

    print("Killing ngrok")
    if platform.system() == "Windows":
        subprocess.run(['taskkill', '/F', '/T', '/PID', str(ngrok_process.pid)], shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    else:
        subprocess.run(['kill', '-9', str(ngrok_process.pid)], shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
    sys.exit()

def open_file_dialog():
    file_path = filedialog.askopenfilename(filetypes=[("JAR files", "*.jar")])
    if file_path:
        jar_file_entry.delete(0, tk.END)
        jar_file_entry.insert(0, file_path)

def execute_server_start():
    jar_file = jar_file_entry.get()
    ram = ram_entry.get()
    root.withdraw()
    start_server(jar_file, ram)
    
def save_config():
    config_to_save = {
        "jar_file": jar_file_entry.get(),
        "ram": ram_entry.get()
    }
    
    file_path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON files", "*.json")])
    if file_path:
        with open(file_path, "w") as config_file:
            json.dump(config_to_save, config_file)

def load_config():
    file_path = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")])
    if file_path:
        with open(file_path, "r") as config_file:
            loaded_config = json.load(config_file)
            jar_file_entry.delete(0, tk.END)
            ram_entry.delete(0, tk.END)
            jar_file_entry.insert(0, loaded_config["jar_file"])
            ram_entry.insert(0, loaded_config["ram"])


root = tk.Tk()
root.iconbitmap("icon.ico")
root.title("Minecraft Server Starter")
root.geometry("200x245")
root.resizable(False,False)

style = ttk.Style()
style.configure("TButton", padding=(10, 5))
style.configure("TLabel", padding=(0, 5))

jar_file_label = ttk.Label(root, text="Select JAR file:")
jar_file_label.pack()
jar_file_entry = ttk.Entry(root)
jar_file_entry.pack()
browse_button = ttk.Button(root, text="Browse", command=open_file_dialog)
browse_button.pack()

ram_label = ttk.Label(root, text="RAM (GB):")
ram_label.pack()
ram_entry = ttk.Entry(root)
ram_entry.pack()

start_button = ttk.Button(root, text="Start Server", command=execute_server_start)
start_button.pack()

save_button = ttk.Button(root, text="Save Config", command=save_config)
load_button = ttk.Button(root, text="Load Config", command=load_config)

save_button.pack()
load_button.pack()

root.mainloop()
