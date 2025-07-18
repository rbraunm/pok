import os
import sys
import subprocess

# --- Ensure dependencies are installed ---
def ensure(module, pipName=None):
  try:
    __import__(module)
  except ImportError:
    pipName = pipName or module
    print(f"Module '{module}' not found. Installing '{pipName}'...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", pipName])
    print(f"'{pipName}' installed successfully.\n")

ensure("paramiko")
ensure("scp")
ensure("keyring")

import paramiko
import getpass
import keyring
from scp import SCPClient

# --- Configuration ---
SSH_HOST = "10.111.111.211"
SSH_USER = "eqemu"
REMOTE_PATH = "pok"
CRED_SERVICE = f"deploy:{SSH_USER}@{SSH_HOST}"

# --- Get password from keyring or prompt ---
def getPassword():
  return keyring.get_password(CRED_SERVICE, SSH_USER)

def promptAndStorePassword():
  pw = getpass.getpass(f"Enter SSH password for {SSH_USER}@{SSH_HOST}: ")
  keyring.set_password(CRED_SERVICE, SSH_USER, pw)
  return pw

# --- Attempt to connect with retries ---
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
    print("Authentication failed.")
    if attempt == 2:
      sys.exit("Too many failed attempts. Exiting.")
    keyring.delete_password(CRED_SERVICE, SSH_USER)
    password = None
  except Exception as e:
    sys.exit(f"SSH connection error: {e}")

# --- Prepare remote directory ---
print(f"Preparing ~/{REMOTE_PATH} on remote...")

checkCmd = f"test -d ~/{REMOTE_PATH}"
stdin, stdout, stderr = ssh.exec_command(checkCmd)
exitStatus = stdout.channel.recv_exit_status()

if exitStatus == 0:
  print(f"Remote path ~/{REMOTE_PATH} exists. Deleting its contents...")
  clearCmd = f"rm -rf ~/{REMOTE_PATH}/*"
  stdin, stdout, stderr = ssh.exec_command(clearCmd)
  errors = stderr.read().decode().strip()
  if errors:
    ssh.close()
    sys.exit(f"Error clearing ~/{REMOTE_PATH}: {errors}")
else:
  print(f"Remote path ~/{REMOTE_PATH} does not exist. Creating it...")
  createCmd = f"mkdir -p ~/{REMOTE_PATH}"
  stdin, stdout, stderr = ssh.exec_command(createCmd)
  errors = stderr.read().decode().strip()
  if errors:
    ssh.close()
    sys.exit(f"Error creating ~/{REMOTE_PATH}: {errors}")

# --- Exclusion logic ---
def isValidPath(path):
  parts = os.path.normpath(path).split(os.sep)
  for i in range(len(parts) - 1):
    if parts[i].startswith("."):
      return False
  filename = parts[-1]
  return filename not in {"README.md", "pok.code-workspace"}

# --- Upload files ---
print("Uploading files...")
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

        # Ensure the remote directory exists (but avoid duplicates)
        if remoteDir not in createdDirs:
          ssh.exec_command(f"mkdir -p ~/{remoteDir}")
          createdDirs.add(remoteDir)

        print(f"Uploading ~/{remotePath}")
        scp.put(fullPath, remote_path=remotePath)

# --- Run remote Docker commands ---
print("Performing docker compose up/down...")
for cmd in ["docker compose down", "docker compose build --no-cache && docker compose up -d"]:
  fullCmd = f"cd ~/{REMOTE_PATH} && {cmd}"
  stdin, stdout, stderr = ssh.exec_command(fullCmd)
  print(stdout.read().decode(), end="")
  print(stderr.read().decode(), end="")

ssh.close()
print("Deployment complete.")
