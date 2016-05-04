#!/usr/bin/env python
# md5: de79926b7d364389c370d99dcce51f2f
# coding: utf-8

import leveldb
import msgpack


leveldbmemoized_basedir = 'leveldb_memoized'

def set_leveldbmemoized_basedir(basedir):
  global leveldbmemoized_basedir
  leveldbmemoized_basedir = basedir


class leveldbmemoized(object):
  def __init__(self, f):
    self.f = f
    self.db = None
  def __call__(self, arg):
    if self.db == None:
      filename = leveldbmemoized_basedir + '/' + self.f.__name__ + '.db'
      self.db = leveldb.LevelDB(filename)
    try:
      return msgpack.loads(self.db.Get(str(arg)))
    except KeyError:
      result = self.f(arg)
      self.db.Put(str(arg), msgpack.dumps(result))
      return result




