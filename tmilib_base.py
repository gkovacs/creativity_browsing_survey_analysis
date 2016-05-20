#!/usr/bin/env python
# md5: f4bc6548ba3d813fd55aca904c344fff
# coding: utf-8

import urlparse
from glob import glob

import os
from os import path

#import decompress_lzstring
import numpy
import pyximport
pyximport.install(setup_args={"include_dirs":numpy.get_include()})
from decompress_lzstring_base64_cython import decompressFromBase64

from memoized import memoized

import msgpack
try:
  import ujson as json
except:
  import json

from collections import Counter
import time
import datetime
import random
from operator import itemgetter
import heapq
import itertools

from sorted_collection import SortedCollection
from math import log





tmi_overrides = {
  'basedir': None,
}

@memoized
def get_basedir():
  if tmi_overrides['basedir'] != None:
    return tmi_overrides['basedir']
  pathbase = '/home/gkovacs'
  if not path.exists('/home/gkovacs'):
    if path.exists('/home/geza'):
      pathbase = '/home/geza'
    elif path.exists('/Users/geza'):
      pathbase = '/Users/geza'
    elif path.exists('/afs/.ir/users/g/k/gkovacs'):
      pathbase = '/afs/.ir/users/g/k/gkovacs'
  output = [x for x in glob(pathbase + '/tmi-data/local_*') if path.isfile(x + '/active')]
  output.sort(reverse=True)
  return output[0]
  #return '/home/gkovacs/tmi-data/latest'

@memoized
def list_logfiles():
  return glob(get_basedir() + '/logs_*.json')

@memoized
def list_mlogfiles():
  return glob(get_basedir() + '/mlogs_*.json')

@memoized
def list_histfiles():
  return glob(get_basedir() + '/hist_*.json')

@memoized
def list_users():
  #return [filename_to_username(x) for x in list_logfiles()]
  return list_users_with_log_and_mlog_and_hist()

@memoized
def list_users_with_hist():
  return [filename_to_username(x) for x in list_histfiles()]

@memoized
def list_users_with_mlog():
  return [filename_to_username(x) for x in list_mlogfiles()]

@memoized
def list_users_with_log():
  return [filename_to_username(x) for x in list_logfiles()]

@memoized
def list_users_with_log_and_hist():
  users_with_hist_set = set(list_users_with_hist())
  return [x for x in list_users_with_log() if x in users_with_hist_set]

@memoized
def list_users_with_log_and_mlog():
  users_with_mlog_set = set(list_users_with_mlog())
  return [x for x in list_users_with_log() if x in users_with_mlog_set]

@memoized
def list_users_with_log_and_mlog_and_hist():
  users_with_mlog_set = set(list_users_with_mlog())
  users_with_hist_set = set(list_users_with_hist())
  return [x for x in list_users_with_log() if x in users_with_mlog_set and x in users_with_hist_set]



@memoized
def get_sdir():
  #return get_basedir().replace('local_', 'sdir_')
  return get_basedir().replace('tmi-data', 'tmi-sdir').replace('local_', 'sdir_')

def ensure_sdir_exists():
  sdir = get_sdir()
  if path.exists(sdir):
    return
  os.makedirs(sdir)

def ensure_sdir_subdir_exists(subdir):
  ensure_sdir_exists()
  sdir = get_sdir()
  if path.exists(sdir + '/' + subdir):
    return
  os.makedirs(sdir + '/' + subdir)

def sdir_path(filename):
  return get_sdir() + '/' + filename

def sdir_glob(filename):
  return glob(get_sdir() + '/' + filename)

def sdir_exists(filename):
  return path.exists(sdir_path(filename))

def sdir_open(filename, mode='r'):
  return open(sdir_path(filename), mode)

def sdir_loadjson(filename):
  return json.load(sdir_open(filename))

def sdir_loadmsgpack(filename):
  return msgpack.load(sdir_open(filename))

def sdir_loadjsonlines(filename):
  jfile = sdir_open(filename)
  for line in jfile:
    yield json.loads(line)
  #line = jfile.readline()
  #while line != None:
  #  yield json.loads(line)
  #  line = jfile.readline()

def sdir_dumpjson(filename, data):
  ensure_sdir_exists()
  return json.dump(data, sdir_open(filename, 'w'))

def sdir_dumpmsgpack(filename, data):
  ensure_sdir_exists()
  return msgpack.dump(data, sdir_open(filename, 'w'))

def sdir_dumpjsonlines(filename, data):
  ensure_sdir_exists()
  outfile = sdir_open(filename, 'w')
  for line in data:
    outfile.write(json.dumps(line))
    outfile.write('\n')
  outfile.close()





def dumpdir_path(filename):
  return get_basedir() + '/' + filename

def get_logfile_for_user(user):
  return dumpdir_path('logs_' + user + '.json')

def get_mlogfile_for_user(user):
  return dumpdir_path('mlogs_' + user + '.json')

def get_histfile_for_user(user):
  return dumpdir_path('hist_' + user + '.json')


def filename_to_username(filename):
  if not filename.endswith('.json'):
    raise Exception('expected filename to end with .json ' + filename)
  filename = filename[:-5] # removes the .json
  return filename.split('_')[-1] # returns part after the last _ which is the username


def decompress_data_lzstring_base64(data):
  data_type = type(data)
  if data_type == unicode or data_type == str:
    return json.loads(decompressFromBase64(data))
  return data

def uncompress_data_subfields(x):
  if 'windows' in x:
    data_type = type(x['windows'])
    if data_type == unicode or data_type == str:
      x['windows'] = json.loads(decompressFromBase64(x['windows']))
  if 'data' in x:
    data_type = type(x['data'])
    if data_type == unicode or data_type == str:
      x['data'] = json.loads(decompressFromBase64(x['data']))
  return x

def iterate_data_jsondata(data):
  for x in data:
    yield uncompress_data_subfields(x)

def iterate_data(filename):
  for x in json.load(open(filename)):
    yield uncompress_data_subfields(x)

def iterate_data_timesorted(filename):
  alldata = json.load(open(filename))
  alldata.sort(key=itemgetter('time'))
  for x in alldata:
    yield uncompress_data_subfields(x)

def iterate_data_compressed_timesorted(filename):
  alldata = json.load(open(filename))
  alldata.sort(key=itemgetter('time'))
  return alldata

def iterate_data_compressed(filename):
  return json.load(open(filename))

def iterate_data_jsondata_reverse(data):
  for x in reversed(data):
    yield uncompress_data_subfields(x)

def iterate_data_reverse(filename):
  alldata = json.load(open(filename))
  alldata.reverse()
  for x in alldata:
    yield uncompress_data_subfields(x)

def iterate_data_compressed_reverse(filename):
  alldata = json.load(open(filename))
  alldata.reverse()
  return alldata



def print_counter(counter, **kwargs):
  num = kwargs.get('num', 100)
  keys_and_values = [{'key': k, 'val': v} for k,v in counter.viewitems()]
  keys_and_values.sort(key=itemgetter('val'), reverse=True)
  for item in keys_and_values[:num]:
    print item['key'], item['val']


def url_to_domain(url):
  return urlparse.urlparse(url).netloc


def shuffled(l):
  l = l[:]
  random.shuffle(l)
  return l


def zipkeys(data, *args):
  return zip(*(data[x] for x in args))

def zipkeys_idx(data, *args):
  return zip(itertools.count(), *(data[x] for x in args))





def sum_values_in_list_of_dict(list_of_dict):
  output = Counter()
  for d in list_of_dict:
    for k,v in d.viewitems():
      output[k] += v
  return output


def orderedMerge(*iterables, **kwargs):
  # from http://stackoverflow.com/questions/464342/combining-two-sorted-lists-in-python
  """Take a list of ordered iterables; return as a single ordered generator.

  @param key:     function, for each item return key value
          (Hint: to sort descending, return negated key value)

  @param unique:  boolean, return only first occurrence for each key value?
  """
  key     = kwargs.get('key', (lambda x: x))
  unique  = kwargs.get('unique', False)

  _heapify       = heapq.heapify
  _heapreplace   = heapq.heapreplace
  _heappop       = heapq.heappop
  _StopIteration = StopIteration

  # preprocess iterators as heapqueue
  h = []
  for itnum, it in enumerate(map(iter, iterables)):
    try:
      next  = it.next
      data   = next()
      keyval = key(data)
      h.append([keyval, itnum, data, next])
    except _StopIteration:
      pass
  _heapify(h)

  # process iterators in ascending key order
  oldkeyval = None
  while True:
    try:
      while True:
        keyval, itnum, data, next = s = h[0]  # get smallest-key value
                            # raises IndexError when h is empty
        # if unique, skip duplicate keys
        if unique and keyval==oldkeyval:
          pass
        else:
          yield data
          oldkeyval = keyval

        # load replacement value from same iterator
        s[2] = data = next()        # raises StopIteration when exhausted
        s[0] = key(data)
        _heapreplace(h, s)          # restore heap condition
    except _StopIteration:
      _heappop(h)                     # remove empty iterator
    except IndexError:
      return




