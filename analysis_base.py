#!/usr/bin/env python
# md5: 2b9681577fdcbfae98e62e2b8813b2d5
# coding: utf-8

import urlparse
from glob import glob
import os
from os import path

from leveldbmemoized import leveldbmemoized, set_leveldbmemoized_basedir
from msgpackmemoized import msgpackmemoized, set_msgpackmemoized_basedir

from memoized import memoized
import numpy

try:
  import ujson as json
except:
  import json

from collections import Counter
from operator import itemgetter

import pyximport
pyximport.install(setup_args={"include_dirs":numpy.get_include()})
from decompress_lzstring_base64_cython import decompressFromBase64


tmi_basedir_override = None
def set_tmi_basedir(basedir):
  global tmi_basedir_override
  tmi_basedir_override = basedir

@memoized
def get_basedir():
  if tmi_basedir_override != None:
    return tmi_basedir_override
  pathbase = path.dirname(path.realpath('__file__'))
  output = [x for x in glob(pathbase + '/browsingsurvey_*')]
  output.sort(reverse=True)
  return output[0]

@memoized
def get_sdir():
  return get_basedir().replace('/browsingsurvey_', '/cached_')


if not path.exists(get_sdir()):
  os.mkdir(get_sdir())
set_leveldbmemoized_basedir(get_sdir())
set_msgpackmemoized_basedir(get_sdir())



def get_basedir_file(filename):
  return get_basedir() + '/' + filename

def jsonload_basedir_file(filename):
  return json.load(open(get_basedir_file(filename)))


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

@memoized
def get_history_pages():
  return [uncompress_data_subfields(x) for x in jsonload_basedir_file('history_pages.json')]

@memoized
def get_history_visits():
  return [uncompress_data_subfields(x) for x in jsonload_basedir_file('history_visits.json')]

@memoized
def get_survey_results():
  return jsonload_basedir_file('surveyresults.json')

@memoized
def get_user_to_hist_pages():
  output = {}
  for line in get_history_pages():
    if 'user' not in line:
      continue
    user = line['user']
    if user not in output:
      output[user] = []
    output[user].append(line)
  return output

@memoized
def get_user_to_hist_visits():
  output = {}
  for line in get_history_visits():
    if 'user' not in line:
      continue
    user = line['user']
    if user not in output:
      output[user] = []
    output[user].append(line)
  return output

def iterate_hist_pages_for_user(user):
  return get_user_to_hist_pages()[user]

def iterate_hist_visits_for_user(user):
  return get_user_to_hist_visits()[user]


@leveldbmemoized
def get_history_valid_hids_for_user(user):
  hid_with_history_pages = set()
  hid_to_totalparts = {}
  hid_to_seenparts = {}
  hid_with_complete_history_visits = set()
  for line in iterate_hist_pages_for_user(user):
    hid = line['hid']
    hid_with_history_pages.add(hid)
  for line in iterate_hist_visits_for_user(user):
    hid = line['hid']
    totalparts = line['totalparts']
    idx = line['idx']
    if totalparts < 1:
      raise 'have totalparts value less than one of ' + str(totalparts) + ' for user ' + user
    if hid not in hid_to_totalparts:
      hid_to_totalparts[hid] = totalparts
    else:
      if hid_to_totalparts[hid] != totalparts:
        raise 'inconsistent totalparts for user ' + user + ' on hid ' + str(hid) + ' with values ' + str(totalparts) + ' and ' + str(hid_to_totalparts[hid])
    if hid not in hid_to_seenparts:
      hid_to_seenparts[hid] = set()
    hid_to_seenparts[hid].add(idx)
    num_parts_seen_so_far = len(hid_to_seenparts[hid])
    if num_parts_seen_so_far > totalparts:
      raise 'num parts seen so far ' + str(num_parts_seen_so_far) + ' is greater than totalparts ' + str(totalparts) + ' for user ' + user
    if num_parts_seen_so_far == totalparts:
      hid_with_complete_history_visits.add(hid)
  output = [hid for hid in hid_with_complete_history_visits if hid in hid_with_history_pages]
  output.sort()
  return output


@leveldbmemoized
def get_history_pages_for_user(user):
  valid_hids = get_history_valid_hids_for_user(user)
  if len(valid_hids) == 0:
    return []
  target_hid = max(valid_hids)
  for line in iterate_hist_pages_for_user(user):
    hid = line['hid']
    if hid != target_hid:
      continue
    data = line['data']
    return data
  return []

@leveldbmemoized
def get_history_visits_for_user(user):
  valid_hids = get_history_valid_hids_for_user(user)
  if len(valid_hids) == 0:
    return {}
  target_hid = max(valid_hids)
  output = {}
  for line in iterate_hist_visits_for_user(user):
    hid = line['hid']
    if hid < target_hid:
      continue
    data = line['data']
    for k,v in data.viewitems():
      output[k] = v
  return output



@memoized
def get_survey_results_by_user():
  output = {}
  for line in get_survey_results():
    if 'id' not in line:
      continue
    username = line['id']
    output[username] = line
  return output

def get_survey_results_for_user(user):
  return get_survey_results_by_user()[user]

@msgpackmemoized
def list_users():
  history_pages_by_user = get_user_to_hist_pages()
  history_visits_by_user = get_user_to_hist_visits()
  survey_results_by_user = get_survey_results_by_user()
  users = survey_results_by_user.keys()
  return [x for x in users if x in history_pages_by_user and x in history_visits_by_user]

@memoized
def get_results_by_user():
  fields = {
    'history_pages': get_history_pages_for_user,
    'history_visits': get_history_visits_for_user,
    'survey_results': get_survey_results_for_user
  }
  output = {}
  for user in list_users():
    output[user] = {k: v(user) for k,v in fields.viewitems()}
  return output


def url_to_domain(url):
  return urlparse.urlparse(url).netloc

def print_counter(counter, **kwargs):
  num = kwargs.get('num', 100)
  keys_and_values = [{'key': k, 'val': v} for k,v in counter.viewitems()]
  keys_and_values.sort(key=itemgetter('val'), reverse=True)
  for item in keys_and_values[:num]:
    print item['key'], item['val']


def compute_per_user(func):
  output = {}
  results_by_user = get_results_by_user()
  for user in list_users():
    output[user] = func(user)
  return output

@leveldbmemoized
def get_history_ordered_visits_for_user(user):
  url_to_visits = get_history_visits_for_user(user)
  ordered_visits = []
  for url,visits in url_to_visits.viewitems():
    for visit in visits:
      visit['url'] = url
    ordered_visits.extend(visits)
  ordered_visits.sort(key=itemgetter('visitTime'))
  return ordered_visits

@leveldbmemoized
def get_domain_to_num_history_visits_for_user(user):
  output = Counter()
  for url,visits in get_history_visits_for_user(user).viewitems():
    domain = url_to_domain(url)
    output[domain] += len(visits)
  return output




