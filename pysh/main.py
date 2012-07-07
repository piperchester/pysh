import os
import re
import sys
import StringIO

SHELL_PREFIX = re.compile(r'^([ \t\f\v]*)>[ \t\f\v]*')

SIGNATURE = ('# -*- coding: utf-8 -*-\n'
             '# This file was auto-generated by pysh.\n'
             '# Don\'t edit this by hand.\n')


class RoughLexer(object):
  def __init__(self, reader):
    self.reader = reader
    self.c = None

  def is_space(self, c):
    return c == ' ' or c == '\t' or c == '\f' or c == '\v'

  def read(self):
    self.c = self.reader.read(1)
    return self.c

  def seek_string_literal(self, content):
    first = self.c
    self.read()
    if self.c == first:
      if self.read() != first:
        # empty literal
        content.write(first * 2)
      else:
        content.write(first * 3)
        self.read()
        self.seek_here_document(content, first)
    else:
      content.write(first)
      self.seek_simple_string_literal(content, first)

  def seek_here_document(self, content, quote):
    count = 0
    while True:
      cur = self.c
      self.read()
      if cur == '':
        raise Exception('EOF while scanning here document')
      elif cur == quote:
        content.write(cur)
        count += 1
        if count == 3:
          break
      elif cur == '\\':
        if self.c == '\r' or self.c == '\n':
          self.seek_backslash(content)
        else:
          content.write('\\' + self.c)
          self.read()
      else:
        content.write(cur)
        count = 0

  def seek_simple_string_literal(self, content, quote):
    while True:
      cur = self.c
      self.read()
      if cur == '':
        raise Exception('EOF while scanning string literal')
      elif cur == '\r' or cur == '\n':
        raise Exception('EOL while scanning string literal')
      elif cur == '\\':
        if self.c == '\r' or self.c == '\n':
          self.seek_backslash(content)
        else:
          content.write('\\' + self.c)
          self.read()
      else:
        content.write(cur)
        if cur == quote:
          break

  def seek_backslash(self, writer):
    if self.c == '\n':
      self.read()
    elif self.c == '\r':
      if self.read() == '\n':
        self.read()
    else:
      writer.write('\\')

  def next(self):
    if self.c is None:
      self.c = self.reader.read(1)

    indent = StringIO.StringIO()
    while self.is_space(self.c):
      indent.write(self.c)
      self.read()

    mode = 'python'
    if self.c == '>':
      mode = 'shell'
      while self.is_space(self.read()):
        pass
      
    content = StringIO.StringIO()
    while True:
      if self.c == '':
        break
      elif self.c == '\'' or self.c == '"':
        self.seek_string_literal(content)
      elif self.c == '#':
        while self.c != '\n' and self.c != '':
          self.read()
        self.read() # discard '\n'
        break
      elif self.c == '\r':
        if self.read() == '\n':
          self.read() # discard '\n'
        break
      elif self.c == '\n':
        self.read() # discard '\n'
        break
      elif self.c == '\\':
        self.read()
        self.seek_backslash(content)
      else:
        content.write(self.c)
        self.read()
    content_value = content.getvalue()
    if self.c == '' and not content_value:
      return None, None, None
    else:
      return indent.getvalue(), mode, content_value


class Converter(object):
  def __init__(self, reader, writer):
    self.lexer = RoughLexer(reader)
    self.writer = writer

  def convert(self):
    self.writer.write('import pysh.pysh\n')
    use_existing = False
    while True:
      if not use_existing:
        indent, mode, content = self.lexer.next()
      else:
        use_existing = False
        
      if indent is None:
        break

      self.writer.write(indent)
      if mode == 'python':
        self.writer.write(content)
      else:
        self.writer.write('pysh.pysh.run(%s, locals(), globals())' % `content`)
      self.writer.write('\n')


def usage_exit():
  print >> sys.stderr, 'Usage: pysh [-c cmd | file | -]'
  sys.exit(1)


def main():
  if len(sys.argv) < 2:
    usage_exit()
  if sys.argv[1] == '-':
    reader = sys.stdin
    writer = StringIO.StringIO()
    Converter(reader, writer).convert()
    argv = sys.argv[2:]
    os.execlp('python', 'python', '-c', writer.getvalue(), *argv)
  elif sys.argv[1] == '-c':
    if len(sys.argv) < 3:
      usage_exit()
    reader = StringIO.StringIO(sys.argv[2])
    writer = StringIO.StringIO()
    Converter(reader, writer).convert()
    argv = sys.argv[3:]
    os.execlp('python', 'python', '-c', writer.getvalue(), *argv)
  else:
    script = sys.argv[1]
    name, ext = os.path.splitext(script)
    if ext == ".py":
      print >> sys.stderr, 'An input file shoundn\'t be *.py.'
      sys.exit(1)
    py = name + '.py'
    reader = file(script, 'r')
    writer = file(py, 'w')
    writer.write(SIGNATURE)
    Converter(reader, writer).convert()
    writer.close()
    argv = sys.argv[2:]
    os.execlp('python', 'python', py, *argv)


if __name__ == '__main__':
  main()
