import sys, os, stat

class DaemoniseException(Exception):
  pass

def write_pid(pid_file):
  # do we require a safe version of this?
  f = open(pid_file, "w")
  try:
    f.write("%d" % os.getppid())
  finally:
    f.close()

def daemonise(stdin=os.devnull, stdout=os.devnull, stderr=os.devnull):
  sys.stdout.flush()
  sys.stderr.flush()

  pid = os.fork()
  if pid:
    sys.exit(0)

  os.setsid()

  pid = os.fork()
  if pid:
    sys.exit(0)

  os.chdir("/")
  os.umask(0)

def close_fds(stdin=os.devnull, stdout=os.devnull, stderr=os.devnull):
  os.close(sys.stdin.fileno())
  os.close(sys.stdout.fileno())
  os.close(sys.stderr.fileno())

  stdin_ = os.open(stdin, os.O_RDWR)
  stdout_ = os.open(stdin, os.O_RDWR)
  stderr_ = os.open(stdin, os.O_RDWR)

  # dup2 closes the fd if required
  os.dup2(stdin_, sys.stdin.fileno())
  os.dup2(stdout_, sys.stdout.fileno())
  os.dup2(stderr_, sys.stderr.fileno())
