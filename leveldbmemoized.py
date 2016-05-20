#!/usr/bin/env python
# md5: 61d09d29b8d0546ca71b941e5ecc66fe
# coding: utf-8

import leveldb
import msgpack


leveldbmemoized_basedir = 'leveldb_memoized'

def set_leveldbmemoized_basedir(basedir):
  global leveldbmemoized_basedir
  leveldbmemoized_basedir = basedir

def get_leveldbmemoized_basedir(basedir):
  return leveldbmemoized_basedir


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




