#!/usr/bin/env python
import subprocess
import platform
import time
import urllib.request
import json
import sys
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import atexit
import socket
import hashlib
import threading


def check_java():
    try:
        result = subprocess.run(['java', '-version'],
                                capture_output=True, text=True)
        if result.returncode == 0:
            print("Java is installed:", result.stdout.strip())
        else:
            messagebox.showwarning(
                "Java Not Found", "Java is not installed. Please install Java to run this program.")
            sys.exit(1)
    except FileNotFoundError:
        messagebox.showwarning(
            "Java Not Found", "Java is not installed. Please install Java to run this program.")
        sys.exit(1)


def check_ngrok():
    try:
        result = subprocess.run(['ngrok', 'version'],
                                capture_output=True, text=True)
        if result.returncode == 0:
            print("ngrok is installed:", result.stdout.strip())
        else:
            messagebox.showwarning(
                "ngrok Not Found", "ngrok is not installed. Please install ngrok to use ngrok functionality.")
    except FileNotFoundError:
        messagebox.showwarning(
            "ngrok Not Found", "ngrok is not installed. Please install ngrok to use ngrok functionality.")


def fetch_version_manifest():
    try:
        with urllib.request.urlopen("https://launchermeta.mojang.com/mc/game/version_manifest.json") as response:
            manifest = json.load(response)
        return manifest
    except Exception as e:
        messagebox.showerror(
            "Error", f"Failed to fetch version manifest: {str(e)}")
        return None


def fetch_paper_manifest():
    try:
        with urllib.request.urlopen("https://papermc.io/api/v2/projects/paper") as response:
            data = json.load(response)
        return data
    except Exception as e:
        messagebox.showerror(
            "Error", f"Failed to fetch paper versions: {str(e)}")
        return None


def fetch_purpur_manifest():
    try:
        url = "https://api.purpurmc.org/v2/purpur/"
        req = urllib.request.Request(url, headers={'User-Agent': 'curl/8.7.1'})
        with urllib.request.urlopen(req) as response:
            data = json.load(response)
        return data
    except Exception as e:
        messagebox.showerror(
            "Error", f"Failed to fetch purpur versions: {str(e)}")
        return None


def fetch_paper_version_latest_build(version):
    try:
        with urllib.request.urlopen(f"https://papermc.io/api/v2/projects/paper/versions/{version}") as response:
            data = json.load(response)
            builds = data["builds"]
            latest_build = max(builds)
            return latest_build
    except Exception as e:
        messagebox.showerror(
            "Error", f"Failed to fetch paper builds: {str(e)}")
        return None


def fetch_purpur_version_latest_build(version):
    try:
        url = f"https://api.purpurmc.org/v2/purpur/{version}"
        req = urllib.request.Request(url, headers={'User-Agent': 'curl/8.7.1'})
        with urllib.request.urlopen(req) as response:
            data = json.load(response)
            builds = data["builds"]
            return builds["latest"]
    except Exception as e:
        messagebox.showerror(
            "Error", f"Failed to fetch purpur builds: {str(e)}")
        return None


def fetch_paper_build_info(version, build):
    try:
        with urllib.request.urlopen(f"https://papermc.io/api/v2/projects/paper/versions/{version}/builds/{build}") as response:
            data = json.load(response)
            return data
    except Exception as e:
        messagebox.showerror(
            "Error", f"Failed to fetch paper build info: {str(e)}")
        return None


def fetch_purpur_build_info(version, build):
    try:
        url = f"https://api.purpurmc.org/v2/purpur/{version}/{build}"
        req = urllib.request.Request(url, headers={'User-Agent': 'curl/8.7.1'})
        with urllib.request.urlopen(req) as response:
            data = json.load(response)
            return data
    except Exception as e:
        messagebox.showerror(
            "Error", f"Failed to fetch purpur build info: {str(e)}")
        return None


def download_server_version(version_info, save_directory, progress_callback, done_callback):
    try:
        isCustom = False
        if isinstance(version_info, str):
            if version_info.startswith("Paper "):
                isCustom = True
                version = version_info.replace("Paper ", "")
                paper_info = fetch_paper_build_info(
                    version, fetch_paper_version_latest_build(version))
                download_info = {}
                download_info["url"] = f"https://papermc.io/api/v2/projects/paper/versions/{version}/builds/{fetch_paper_version_latest_build(version)}/downloads/{paper_info['downloads']['application']['name']}"
                download_info["sha256"] = paper_info["downloads"]["application"]["sha256"]
                download_info["filename"] = paper_info["downloads"]["application"]["name"]
            elif version_info.startswith("Purpur "):
                isCustom = True
                version = version_info.replace("Purpur ", "")
                latest_build = fetch_purpur_version_latest_build(version)
                purpur_info = fetch_purpur_build_info(version, latest_build)
                download_info = {}
                download_info["url"] = f"https://api.purpurmc.org/v2/purpur/{version}/{latest_build}/download"
                download_info["md5"] = purpur_info["md5"]
                download_info["filename"] = "purpur-" + \
                    version + "-" + latest_build + ".jar"

        else:
            download_info_url = version_info["url"]

            with urllib.request.urlopen(download_info_url) as response:
                download_info = json.load(response)

        if not isCustom:
            version_url = download_info["downloads"]["server"]["url"]
            version_hash = download_info["downloads"]["server"]["sha1"]
            file_name = "server.jar"
        else:
            version_url = download_info["url"]
            file_name = download_info["filename"]
            if "sha256" in download_info:
                version_hash = download_info["sha256"]
            else:
                version_hash = download_info["md5"]

        save_path = os.path.join(save_directory, file_name).replace("\\", "/")

        def report_hook(count, block_size, total_size):
            progress = min(int(count * block_size * 100 / total_size), 100)
            progress_callback(progress)

        opener = urllib.request.build_opener()
        opener.addheaders = [('User-agent', 'Curl/8.7.1')]
        urllib.request.install_opener(opener)

        urllib.request.urlretrieve(
            version_url, save_path, reporthook=report_hook)

        if not isCustom:
            with open(save_path, "rb") as f:
                sha1 = hashlib.sha1()
                while True:
                    data = f.read(65536)
                    if not data:
                        break
                    sha1.update(data)

            downloaded_hash = sha1.hexdigest()
        else:
            if "sha256" in download_info:
                with open(save_path, "rb") as f:
                    sha256 = hashlib.sha256()
                    while True:
                        data = f.read(65536)
                        if not data:
                            break
                        sha256.update(data)

                downloaded_hash = sha256.hexdigest()
            else:
                with open(save_path, "rb") as f:
                    md5 = hashlib.md5()
                    while True:
                        data = f.read(65536)
                        if not data:
                            break
                        md5.update(data)

                downloaded_hash = md5.hexdigest()

        if downloaded_hash != version_hash:
            messagebox.showerror(
                "Error", f"SHA-1/SHA-256/MD5 hash mismatch for downloaded server jar!")
            os.remove(save_path)
            return None

        done_callback(save_path)

    except Exception as e:
        messagebox.showerror(
            "Error", f"Failed to download and verify server jar: {str(e)}")
        return None


def on_download_click():
    global version_dropdown, download_progress, version_manifest, download_window, paper_manifest, purpur_manifest

    download_window = tk.Toplevel()
    download_window.title("Download Minecraft Server")
    download_window.iconbitmap("icon.ico")
    download_window.geometry("200x120")
    download_window.resizable(False, False)

    version_manifest = fetch_version_manifest()
    paper_manifest = fetch_paper_manifest()
    purpur_manifest = fetch_purpur_manifest()

    if not version_manifest:
        download_window.destroy()
        return

    if not paper_manifest:
        download_window.destroy()
        return

    if not purpur_manifest:
        download_window.destroy()
        return

    vals = [v["id"] for v in version_manifest["versions"]] + ["Paper " +
                                                              v for v in paper_manifest["versions"]] + ["Purpur " + v for v in purpur_manifest["versions"]]

    version_label = ttk.Label(
        download_window, text="Select Minecraft Version:")
    version_label.pack()

    version_dropdown = ttk.Combobox(download_window, values=vals)
    version_dropdown.pack()

    download_button = ttk.Button(
        download_window, text="Download", command=on_download_version)
    download_button.pack()

    download_progress = ttk.Progressbar(
        download_window, orient="horizontal", length=180, mode="determinate")
    download_progress.pack()


def on_download_version():
    global version_dropdown, download_progress, version_manifest, download_window

    selected_version = version_dropdown.get()

    if selected_version.startswith("Paper "):
        for version_info in paper_manifest["versions"]:
            if version_info == selected_version.replace("Paper ", ""):
                version_selected = selected_version
                break
    elif selected_version.startswith("Purpur "):
        for version_info in purpur_manifest["versions"]:
            if version_info == selected_version.replace("Purpur ", ""):
                version_selected = selected_version
                break
    else:
        for version_info in version_manifest["versions"]:
            if version_info["id"] == selected_version:
                version_selected = version_info
                break

        if not version_selected:
            messagebox.showerror("Error", f"Version {selected_version} not found in version manifest.")
            return

    save_directory = filedialog.askdirectory()
    if not save_directory:
        return

    download_progress["value"] = 0

    def update_progress(progress):
        download_progress["value"] = progress

    def done_callback(save_path):
        messagebox.showinfo("Download Complete",
                            f"Server jar downloaded to {save_path}.")
        jar_file_entry.delete(0, tk.END)
        jar_file_entry.insert(0, save_path)
        download_window.destroy()

    download_thread = threading.Thread(target=download_server_version, args=(
        version_selected, save_directory, update_progress, done_callback))
    download_thread.start()

    messagebox.showinfo("Downloading", f"Downloading server jar for version {selected_version}. Please wait...")


def check_and_create_eula(jar_file_directory):
    eula_file_path = os.path.join(
        jar_file_directory, "eula.txt").replace("\\", "/")

    if not os.path.exists(eula_file_path):
        with open(eula_file_path, "w") as eula_file:
            eula_file.write("eula=true")


def get_local_ip(port):
    try:
        hostname = socket.gethostname()
        local_ip = socket.gethostbyname(hostname)
        if port == 25565:
            return local_ip
        else:
            return f"{local_ip}:{port}"
    except socket.gaierror:
        return "Unable to determine local IP"


def start_ngrok(port):
    global ngrok_process
    ngrok_process = subprocess.Popen(['ngrok', 'tcp', str(
        port)], shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(2)
    return ngrok_process


def get_ngrok_url(port):
    with urllib.request.urlopen("http://localhost:4040/api/tunnels") as response:
        data = response.read()
    datajson = json.loads(data)
    for tunnel in datajson['tunnels']:
        public_url = tunnel['public_url']
        port_info = tunnel['config']['addr']
        if port_info.endswith(str(port)):
            return public_url.replace("tcp://", "")
    return None


def copy(txt):
    if platform.system() == "Windows":
        cmd = 'echo ' + txt.strip() + ' | clip'
    if platform.system() == "Darwin":
        cmd = 'echo ' + txt.strip() + ' | pbcopy'
    if platform.system() == "Linux":
        cmd = 'echo ' + txt.strip() + ' | xclip'
    return subprocess.check_call(cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def start_server(jar_file, ram, port, ngrok):
    if ngrok:
        print("Starting ngrok...")
        ngrok_process = start_ngrok(port)

        ngrok_url = get_ngrok_url(port)
        copy(ngrok_url)
        print("Copied ngrok URL \"" + ngrok_url + "\" to Clipboard")
    else:
        copy(get_local_ip(port))
        print("Copied Local IP Address to Clipboard")

    print("Starting Minecraft Server...")

    server_directory = os.path.dirname(jar_file)

    check_and_create_eula(server_directory)

    minecraft_process = subprocess.Popen(['java', '-XX:+UseG1GC', f'-Xmx{ram}M', f'-Xms{ram}M', '-Dsun.rmi.dgc.server.gcInterval=2147483646', '-XX:+UnlockExperimentalVMOptions', '-XX:G1NewSizePercent=20', '-XX:G1ReservePercent=20',
                                         '-XX:MaxGCPauseMillis=50', '-XX:G1HeapRegionSize=32M', '-jar', jar_file], cwd=server_directory, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=subprocess.CREATE_NO_WINDOW)

    minecraft_process.wait()
    print("Server Exited")

    if ngrok:
        print("Killing ngrok")
        if platform.system() == "Windows":
            subprocess.run(['taskkill', '/F', '/T', '/PID', str(ngrok_process.pid)],
                           shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        else:
            subprocess.run(['kill', '-9', str(ngrok_process.pid)], shell=True,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    sys.exit()


def open_file_dialog():
    file_path = filedialog.askopenfilename(filetypes=[("JAR files", "*.jar")])
    if file_path:
        jar_file_entry.delete(0, tk.END)
        jar_file_entry.insert(0, file_path)


def execute_server_start():
    jar_file = jar_file_entry.get()
    ram = ram_entry.get()
    port = port_entry.get() or read_server_port_from_properties(jar_file)
    ngrok = use_ngrok.get()
    root.withdraw()
    start_server(jar_file, ram, port, ngrok)


def read_server_port_from_properties(jar_file):
    server_directory = os.path.dirname(jar_file)
    properties_file_path = os.path.join(
        server_directory, "server.properties").replace("\\", "/")
    if os.path.exists(properties_file_path):
        with open(properties_file_path, "r") as properties_file:
            for line in properties_file:
                if line.startswith("server-port="):
                    return int(line.strip().split("=")[1])
    return 25565


def save_config():
    config_to_save = {
        "jar_file": jar_file_entry.get(),
        "ram": ram_entry.get(),
        "port": port_entry.get(),
        "ngrok": use_ngrok.get()
    }

    file_path = "config.json"
    if file_path:
        with open(file_path, "w") as config_file:
            json.dump(config_to_save, config_file)


def load_config():
    file_path = "config.json"
    if file_path:
        try:
            with open(file_path, "r") as config_file:
                loaded_config = json.load(config_file)
                jar_file_entry.delete(0, tk.END)
                ram_entry.delete(0, tk.END)
                port_entry.delete(0, tk.END)
                jar_file_entry.insert(0, loaded_config["jar_file"])
                ram_entry.insert(0, loaded_config["ram"])
                port_entry.insert(0, loaded_config["port"])
                use_ngrok.set(loaded_config.get("ngrok", True))
        except FileNotFoundError:
            save_config()


def on_closing():
    save_config()
    root.destroy()


check_java()
check_ngrok()

root = tk.Tk()
root.iconbitmap("icon.ico")
root.title("Minecraft Server Starter")
root.geometry("200x285")
root.resizable(False, False)

use_ngrok = tk.BooleanVar()
use_ngrok.set(False)

style = ttk.Style()
style.configure("TButton", padding=(10, 5))
style.configure("TLabel", padding=(0, 5))

jar_file_label = ttk.Label(root, text="Select JAR file:")
jar_file_label.pack()
jar_file_entry = ttk.Entry(root)
jar_file_entry.pack()
browse_button = ttk.Button(root, text="Browse", command=open_file_dialog)
browse_button.pack()

download_button = ttk.Button(root, text="Download", command=on_download_click)
download_button.pack()

ram_label = ttk.Label(root, text="RAM (MB):")
ram_label.pack()
ram_entry = ttk.Entry(root)
ram_entry.pack()

port_label = ttk.Label(root, text="Port:")
port_label.pack()
port_entry = ttk.Entry(root)
port_entry.pack()

use_ngrok_checkbutton = ttk.Checkbutton(
    root, text="Use ngrok", variable=use_ngrok)
use_ngrok_checkbutton.pack()

start_button = ttk.Button(root, text="Start Server",
                          command=execute_server_start)
start_button.pack()

atexit.register(save_config)
load_config()

root.protocol("WM_DELETE_WINDOW", on_closing)

root.mainloop()
