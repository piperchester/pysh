import csv
import os

import pysh.shell.evaluator

def file_to_array(f):
  return map(lambda line: line.rstrip('\r\n'), f.readlines())


class pycmd_send(object):
  def process(self, args, input):
    assert len(args) == 2
    return args[1]


class pycmd_recv(object):
  def process(self, args, input):
    if isinstance(input, file):
      input = file_to_array(input)
    assert len(args) == 2
    l = args[1]
    assert isinstance(l, list)
    l.extend(input)
    return []


class pycmd_map(object):
  def process(self, args, input):
    assert len(args) == 2
    if isinstance(input, file):
      input = file_to_array(input)
    f = args[1]
    assert callable(f)
    return (f(x) for x in input)


class pycmd_filter(object):
  def process(self, args, input):
    assert len(args) == 2
    if isinstance(input, file):
      input = file_to_array(input)
    cond = args[1]
    assert callable(cond)
    for x in input:
      if cond(x):
        yield x


class pycmd_reduce(object):
  def process(self, args, input):
    assert len(args) == 2
    if isinstance(input, file):
      input = file_to_array(input)
    f = args[1]
    assert callable(f)
    return [reduce(f, input)]


class pycmd_readcsv(object):
  def process(self, args, input):
    return csv.reader(input)


class pycmd_cd(object):
  def process(self, args, input):
    assert len(args) == 2
    os.chdir(args[1])
    return ()

def register_builtin():
  register_pycmd = pysh.shell.evaluator.register_pycmd
  register_pycmd('send', pycmd_send())
  register_pycmd('recv', pycmd_recv())
  register_pycmd('map', pycmd_map())
  register_pycmd('filter', pycmd_filter())
  register_pycmd('reduce', pycmd_reduce())
  register_pycmd('readcsv', pycmd_readcsv())
  register_pycmd('cd', pycmd_cd())