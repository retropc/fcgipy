import ConfigParser, os, shlex, pwd, grp, daemonise

class FCGI(object):
  def __init__(self, name, program, args, uid, gid=None):
    super(FCGI, self).__init__()

    self.name = name
    self.program, self.args = program, args
    self.uid, self.gid = uid, gid

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
    os.execv(self.program, args)

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

  items = []
  for section_name in r.sections():
    program = r.get(section_name, "program")
    if r.has_option(section_name, "args"):
      args = shlex.split(r.get(section_name, "args"))
    else:
      args = []

    uid = r.get(section_name, "uid")

    if r.has_option(section_name, "gid"):
      gid = r.get(section_name, "gid")
    else:
      gid = None

    items.append(FCGI(section_name, program=program, args=args, uid=uid, gid=gid))

  return items

if __name__ == "__main__":
  print read_config("fcgipy.conf")
