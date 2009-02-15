import sys, os, stat

def daemonise(pid_file=None):
  if pid_file is not None:
    f = open(pid_file, "w")

  try:
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

    f.write("%d" % os.getpid())
  finally:
    if pid_file is not None:
      f.close()

def close_fds(stdin=os.devnull, stdout=os.devnull, stderr=os.devnull):
  os.close(sys.stdin.fileno())
  os.close(sys.stdout.fileno())
  os.close(sys.stderr.fileno())

  stdin_ = os.open(stdin, os.O_RDWR)
  stdout_ = os.open(stdout, os.O_RDWR)
  stderr_ = os.open(stderr, os.O_RDWR)

  # dup2 closes the fd if required
  os.dup2(stdin_, sys.stdin.fileno())
  os.dup2(stdout_, sys.stdout.fileno())
  os.dup2(stderr_, sys.stderr.fileno())
