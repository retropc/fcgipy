#!/usr/bin/env python
import sys, os, time, traceback

LEAVE_DEAD_SECONDS = 5

class SchedulerException(Exception):
  pass

class Subprocess(object):
  def __init__(self, fcgi):
    super(Subprocess, self).__init__()
    self.fcgi = fcgi
    self._pid = None

  def get_running(self):
    if self._pid is None:
      return False
    return self._pid

  def set_running(self, value):
    if value != False:
      raise SchedulerException, "Bad value, can only set to False."

    self.died_at = time.time()
    self._pid = None
  running = property(get_running, set_running)

  @property
  def pid(self):
    if self._pid is None:
      raise SchedulerException, "Shouldn't be looked up in this state."
    return self._pid

  def run(self):
    pid = os.fork()
    if pid != 0:
      self._pid = pid      
      return

    try:
      self.fcgi.run()
    except:
      print >>sys.stderr, "SOMETHING WENT WRONG EXECUTING %s" % self.fcgi 
      traceback.print_exc()

    sys.exit(1)

  def __str__(self): return "<Subprocesss running: %s fcgi: %s>" % (self.running and "yes" or "no", repr(self.fcgi))
  def __repr__(self): return str(self)

class Scheduler(object):
  def __init__(self, fcgi):
    self.subprocesses = [Subprocess(config_obj) for config_obj in fcgi]

    self.runnable = set(self.subprocesses)
    self.dead = set()
    self.executing = {}

  def run(self):
    self.process_dead()
    self.run_runnable()

  def run_runnable(self):
    runnable = self.runnable

    while runnable:
      obj = runnable.pop()
      try:
        obj.run()

        self.executing[obj.pid] = obj
      except SystemExit: # children do this
        raise
      except OSError:
        traceback.print_exc()
        self.dead.add(obj)

  def process_dead(self):
    if not self.dead:
      return

    t = time.time() - LEAVE_DEAD_SECONDS
    new_dead = set()

    for obj in self.dead:
      if t >= obj.died_at:
        # time to resurrect
        self.runnable.add(obj)
      else:
        new_dead.add(obj)

    self.dead = new_dead

  def reap(self, pid):
    obj = self.executing[pid]
    del self.executing[pid]

    obj.running = False
    self.dead.add(obj)

  def __str__(self):
    def m(x): return [y.fcgi.name for y in x]
    return "<Scheduler executing: %s runnable: %s dead: %s>" % (m(self.executing.values()), m(self.runnable), m(self.dead))
  def __repr__(self): return str(self)
