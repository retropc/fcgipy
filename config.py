import ConfigParser, os, shlex, pwd, grp, daemonise

class FCGI(object):
  def __init__(self, name, core, **kwargs):
    super(FCGI, self).__init__()

    if core:
      for key in kwargs:
        if hasattr(core, key):
          setattr(self, key, getattr(core, key))

    for key, value in kwargs.items():
      setattr(self, key, value)

  def run(self):
    uid, gid, groups = self.lookup_uid(self.uid)
    if self.gid is not None:
      gid = self.lookup_gid(self.gid)

    args = [self.program] + self.args

    os.chdir("/")

    os.setgroups(groups)
    os.setgid(gid)
    os.setuid(uid)

    if set(os.getgroups()) != set(groups):
      raise SecurityException, "setgroups failed!"
    if os.getgid() != gid or os.getegid() != gid:
      raise SecurityException, "setgid failed!"
    if os.getuid() != uid or os.geteuid() != uid:
      raise SecurityException, "setuid failed!"

    os.chdir("/")

    daemonise.close_fds()

    if self.dir:
      os.chdir(self.dir)

    if self.environment_copy is None and self.environment is None:
      os.execv(self.program, args)
    else:
      if self.environment_copy is not None:
        environ_keys = set(os.environ.keys()).intersection(set(self.environment_copy))
        environ = dict((x, os.environ[x]) for x in environ_keys)
      else:
        environ = {}
      if self.environment is not None:
        environ.update(self.environment)

      os.execve(self.program, args, environ)

  @classmethod
  def lookup_uid(cls, uid):
    if uid.isdigit():
      entry = pwd.getpwid(uid)
      username = entry.pw_name
    else:
      entry = pwd.getpwnam(uid)
      username = entry.pw_name
      if username != uid:
        raise SecurityException, "passed username and username from password database do not match."

    group_ids = [group_entry.gr_gid for group_entry in grp.getgrall() if username in group_entry.gr_mem]

    return entry.pw_uid, entry.pw_gid, group_ids

  @classmethod
  def lookup_gid(cls, gid):
    if gid.isdigit():
      return int(gid)

    return grp.getgrnam(uid).gr_gid

  def __str__(self): return "<FCGI name: %s program: %s args: %s uid: %s>" % (self.name, self.program, self.args, self.uid)
  def __repr__(self): return str(self)

def read_config(filename):
  r = ConfigParser.RawConfigParser()
  f = open(filename, "r")
  try:
    r.readfp(f)
  finally:
    f.close()

  def read_section(section_name, core=None):
    cons = {}
    if core is not None:
      cons["program"] = r.get(section_name, "program")
      if r.has_option(section_name, "args"):
        cons["args"] = shlex.split(r.get(section_name, "args"))
      else:
        cons["args"] = []

      cons["uid"] = r.get(section_name, "uid")

      if r.has_option(section_name, "gid"):
        cons["gid"] = r.get(section_name, "gid")
      else:
        cons["gid"] = None

      if r.has_option(section_name, "dir"):
        cons["dir"] = r.get(section_name, "dir")
      else:
        cons["dir"] = None

    if r.has_option(section_name, "environment"):
      environ = {}
      for x in r.get(section_name, "environment").strip().split(" "):
        key, value = x.split("=", 1)
        environ[key] = value
    else:
      environ = None

    cons["environment"] = environ
    
    if r.has_option(section_name, "environment_copy"):
      cons["environment_copy"] = r.get(section_name, "environment_copy").strip().split(" ")
    else:
      cons["environment_copy"] = None
    
    return FCGI(section_name, core, **cons)

  if "core" in r.sections():
    core = read_section("core")
  else:
    core = None

  items = []
  for section_name in r.sections():
    if section_name == "core":
      continue

    items.append(read_section(section_name, core=core))

  return items

if __name__ == "__main__":
  print read_config("fcgipy.conf")
