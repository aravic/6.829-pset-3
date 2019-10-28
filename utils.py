import os


def mkdir_if_not_exists(d):
  os.system('mkdir -p %s' % d)
