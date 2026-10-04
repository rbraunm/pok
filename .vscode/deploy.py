import os
import sys
import subprocess
import datetime
import re
import io
import posixpath
import ctypes
import ctypes.wintypes as wintypes

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

import paramiko

SSH_HOST = "peridot.strata.unseencolor.com"
SSH_USER = "claude"
CREDENTIAL_TARGET = f"claude/{SSH_HOST}"
STAGING_PATH = ".pok-deploy"
APP_OWNER = "eqemu"
APP_PATH = "/opt/eqemu/pok"
KNOWN_HOSTS = os.path.join(os.path.expanduser("~"), ".ssh", "known_hosts")

class credentialRecord(ctypes.Structure):
  _fields_ = [
    ("Flags", wintypes.DWORD),
    ("Type", wintypes.DWORD),
    ("TargetName", wintypes.LPWSTR),
    ("Comment", wintypes.LPWSTR),
    ("LastWritten", wintypes.FILETIME),
    ("CredentialBlobSize", wintypes.DWORD),
    ("CredentialBlob", ctypes.POINTER(ctypes.c_byte)),
    ("Persist", wintypes.DWORD),
    ("AttributeCount", wintypes.DWORD),
    ("Attributes", ctypes.c_void_p),
    ("TargetAlias", wintypes.LPWSTR),
    ("UserName", wintypes.LPWSTR),
  ]

def readCredential(targetName):
  advapi32 = ctypes.WinDLL("advapi32", use_last_error=True)
  pointer = ctypes.POINTER(credentialRecord)()
  if not advapi32.CredReadW(targetName, 1, 0, ctypes.byref(pointer)):
    sys.exit(f"No {targetName} in Windows Credential Manager (error {ctypes.get_last_error()}).")
  try:
    record = pointer.contents
    return record.UserName, ctypes.string_at(record.CredentialBlob, record.CredentialBlobSize).decode("utf-16-le")
  finally:
    advapi32.CredFree(pointer)

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

def run(ssh, command):
  stdin, stdout, stderr = ssh.exec_command(command)
  output = stdout.read().decode().strip()
  errors = stderr.read().decode().strip()
  status = stdout.channel.recv_exit_status()
  if output:
    log(output)
  if errors:
    log(errors)
  if status != 0:
    ssh.close()
    sys.exit(f"'{command}' failed with exit status {status}.")

def isValidPath(path):
  parts = os.path.normpath(path).split(os.sep)
  for i in range(len(parts) - 1):
    if parts[i].startswith("."):
      return False
  filename = parts[-1]
  return filename not in {"README.md", "pok.code-workspace"}

userName, privateKey = readCredential(CREDENTIAL_TARGET)
if userName != SSH_USER:
  sys.exit(f"{CREDENTIAL_TARGET} is for {userName}, not {SSH_USER}.")

ssh = paramiko.SSHClient()
ssh.load_system_host_keys(KNOWN_HOSTS)
ssh.set_missing_host_key_policy(paramiko.RejectPolicy())
try:
  ssh.connect(SSH_HOST, username=SSH_USER, pkey=paramiko.Ed25519Key.from_private_key(io.StringIO(privateKey)),
    look_for_keys=False, allow_agent=False)
except Exception as e:
  sys.exit(f"SSH connection error: {e}")

bumpAppVersion()
log(f"Staging files in ~/{STAGING_PATH}...")
run(ssh, f"rm -rf ~/{STAGING_PATH} && mkdir -p ~/{STAGING_PATH}")
sftp = ssh.open_sftp()
createdDirs = {STAGING_PATH}
for root, dirs, files in os.walk("."):
  if not isValidPath(root):
    continue
  dirs[:] = [d for d in dirs if isValidPath(os.path.join(root, d))]
  for f in files:
    fullPath = os.path.join(root, f)
    if isValidPath(fullPath):
      relPath = os.path.relpath(fullPath, ".")
      remotePath = posixpath.join(STAGING_PATH, relPath.replace("\\", "/"))
      remoteDir = posixpath.dirname(remotePath)
      if remoteDir not in createdDirs:
        run(ssh, f"mkdir -p ~/{remoteDir}")
        createdDirs.add(remoteDir)
      log(f"Uploading {relPath}")
      sftp.put(fullPath, remotePath, confirm=True)
sftp.close()

log(f"Replacing {APP_PATH} with the staged files, owned by {APP_OWNER}...")
run(ssh, f"sudo -n rsync -a --delete --chown={APP_OWNER}:{APP_OWNER} ~/{STAGING_PATH}/ {APP_PATH}/ && rm -rf ~/{STAGING_PATH}")

log("Performing docker compose down, build, and up...")
run(ssh, f"sudo -n -u {APP_OWNER} -H sh -c 'cd {APP_PATH} && docker compose down && docker compose build --no-cache && docker compose up -d'")

ssh.close()
log("Deployment complete.")
