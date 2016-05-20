#!/usr/bin/env python
# md5: 81037534c87b6980a1713954b85c2e4a
# coding: utf-8

import msgpack
#import msgpack_numpy
#msgpack_numpy.patch()
from os import path


msgpackmemoized_basedir = 'msgpack_memoized'

def set_msgpackmemoized_basedir(basedir):
  global msgpackmemoized_basedir
  msgpackmemoized_basedir = basedir

def get_msgpackmemoized_basedir():
  return msgpackmemoized_basedir




# based on http://www.artima.com/weblogs/viewpost.jsp?thread=240845

class msgpackmemoized(object):
  def __init__(self, f):
    self.f = f
    self.filename = None
  def __call__(self):
    if self.filename == None:
      self.filename = msgpackmemoized_basedir + '/' + self.f.__name__ + '.msgpack'
    if path.exists(self.filename):
      return msgpack.load(open(self.filename))
    result = self.f()
    msgpack.dump(result, open(self.filename, 'w'))
    return result

class msgpackmemoized_fileloc(object):
  def __init__(self, filename=None):
    if filename != None:
      if not filename.endswith('.msgpack'):
        filename = filename + '.msgpack'
    self.filename = filename
  def __call__(self, f):
    if self.filename == None:
      self.filename = f.__name__ + '.msgpack'
    def wrapped_f():
      if path.exists(self.filename):
        return msgpack.load(open(self.filename))
      result = f()
      msgpack.dump(result, open(self.filename, 'w'))
      return result
    return wrapped_f


#@msgpackmemoized
#def compute_array():
#  print 'compute_array called'
#  return [3,5,7,9]


#print compute_array()

