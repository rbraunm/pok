import os
import sys
import subprocess
import datetime
import re

def log(message):
  print(f"[{datetime.datetime.now().isoformat(sep=' ', timespec='seconds')}] {message}")

def ensure(module, pipName=None):
  try:
    __import__(module)
  except ImportError:
    pipName = pipName or module
    log(f"Module '{module}' not found. Installing '{pipName}'...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", pipName])
    log(f"'{pipName}' installed successfully.\n")

ensure("paramiko")
ensure("scp")
ensure("keyring")

import paramiko
import getpass
import keyring
from scp import SCPClient

SSH_HOST = "10.111.111.211"
SSH_USER = "eqemu"
REMOTE_PATH = "pok"
CRED_SERVICE = f"deploy:{SSH_USER}@{SSH_HOST}"

def bumpAppVersion():
  appPy = "app/app.py"
  if not os.path.isfile(appPy):
    sys.exit(f"{appPy} not found.")

  with open(appPy, "r", encoding="utf-8") as f:
    lines = f.readlines()

  versionPattern = re.compile(r"^APP_VERSION\s*=\s*['\"](\d+)\.(\d+)\.(\d+)['\"]")
  newLines = []
  updated = False

  for line in lines:
    match = versionPattern.match(line)
    if match:
      major, minor, patch = map(int, match.groups())
      patch += 1
      newVersion = f"{major}.{minor}.{patch}"
      log(f"Bumping APP_VERSION to {newVersion}")
      newLines.append(f'APP_VERSION = "{newVersion}"\n')
      updated = True
    else:
      newLines.append(line)

  if not updated:
    sys.exit("APP_VERSION not found in app.py.")

  with open(appPy, "w", encoding="utf-8") as f:
    f.writelines(newLines)

def getPassword():
  return keyring.get_password(CRED_SERVICE, SSH_USER)

def promptAndStorePassword():
  pw = getpass.getpass(f"Enter SSH password for {SSH_USER}@{SSH_HOST}: ")
  keyring.set_password(CRED_SERVICE, SSH_USER, pw)
  return pw

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

password = getPassword()
for attempt in range(3):
  try:
    if not password:
      password = promptAndStorePassword()
    ssh.connect(SSH_HOST, username=SSH_USER, password=password)
    break
  except paramiko.AuthenticationException:
    log("Authentication failed.")
    if attempt == 2:
      sys.exit("Too many failed attempts. Exiting.")
    keyring.delete_password(CRED_SERVICE, SSH_USER)
    password = None
  except Exception as e:
    sys.exit(f"SSH connection error: {e}")

log(f"Preparing ~/{REMOTE_PATH} on remote...")

checkCmd = f"test -d ~/{REMOTE_PATH}"
stdin, stdout, stderr = ssh.exec_command(checkCmd)
exitStatus = stdout.channel.recv_exit_status()

if exitStatus == 0:
  log(f"Remote path ~/{REMOTE_PATH} exists. Deleting its contents...")
  clearCmd = f"rm -rf ~/{REMOTE_PATH}/*"
  stdin, stdout, stderr = ssh.exec_command(clearCmd)
  errors = stderr.read().decode().strip()
  if errors:
    ssh.close()
    sys.exit(f"Error clearing ~/{REMOTE_PATH}: {errors}")
else:
  log(f"Remote path ~/{REMOTE_PATH} does not exist. Creating it...")
  createCmd = f"mkdir -p ~/{REMOTE_PATH}"
  stdin, stdout, stderr = ssh.exec_command(createCmd)
  errors = stderr.read().decode().strip()
  if errors:
    ssh.close()
    sys.exit(f"Error creating ~/{REMOTE_PATH}: {errors}")

def isValidPath(path):
  parts = os.path.normpath(path).split(os.sep)
  for i in range(len(parts) - 1):
    if parts[i].startswith("."):
      return False
  filename = parts[-1]
  return filename not in {"README.md", "pok.code-workspace"}

bumpAppVersion()
log("Uploading files...")
with SCPClient(ssh.get_transport()) as scp:
  createdDirs = set()
  for root, dirs, files in os.walk("."):
    if not isValidPath(root):
      continue
    dirs[:] = [d for d in dirs if isValidPath(os.path.join(root, d))]
    for f in files:
      fullPath = os.path.join(root, f)
      if isValidPath(fullPath):
        relPath = os.path.relpath(fullPath, ".")
        remotePath = os.path.join(REMOTE_PATH, relPath).replace("\\", "/")
        remoteDir = os.path.dirname(remotePath)

        if remoteDir not in createdDirs:
          ssh.exec_command(f"mkdir -p ~/{remoteDir}")
          createdDirs.add(remoteDir)

        log(f"Uploading ~/{remotePath}")
        scp.put(fullPath, remote_path=remotePath)

log("Performing docker compose up/down...")
for cmd in ["docker compose down", "docker compose build --no-cache && docker compose up -d"]:
  fullCmd = f"cd ~/{REMOTE_PATH} && {cmd}"
  stdin, stdout, stderr = ssh.exec_command(fullCmd)
  log(stdout.read().decode().strip())
  log(stderr.read().decode().strip())

ssh.close()
log("Deployment complete.")
