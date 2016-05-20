#!/usr/bin/env python
# md5: d636f54a4af08eadbb8298acfab7688b
# coding: utf-8

import urlparse
from glob import glob
import os
from os import path

from leveldbmemoized import leveldbmemoized, set_leveldbmemoized_basedir, get_leveldbmemoized_basedir
from msgpackmemoized import msgpackmemoized, set_msgpackmemoized_basedir, get_msgpackmemoized_basedir

from memoized import memoized
import numpy
import yaml

from reconstruct_focus_times import ReconstructFocusTimesBaseline

try:
  import ujson as json
except:
  import json
import msgpack

from collections import Counter
from operator import itemgetter

import pyximport
pyximport.install(setup_args={"include_dirs":numpy.get_include()})
from decompress_lzstring_base64_cython import decompressFromBase64


tmi_basedir_override = None
def set_tmi_basedir(basedir):
  global tmi_basedir_override
  tmi_basedir_override = basedir

tmi_prefix_override = 'browsingsurvey'
def set_tmi_prefix(prefix):
  global tmi_prefix_override
  tmi_prefix_override = prefix

@memoized
def get_basedir():
  if tmi_basedir_override != None:
    return tmi_basedir_override
  pathbase = path.dirname(path.realpath('__file__'))
  output = [x for x in glob(pathbase + '/' + tmi_prefix_override + '_*')]
  output.sort(reverse=True)
  return output[0]

@memoized
def get_sdir():
  return get_basedir().replace('/' + tmi_prefix_override + '_', '/cached_' + tmi_prefix_override + '_')


def initialize_analysis_base():
  if not path.exists(get_sdir()):
    os.mkdir(get_sdir())
  set_leveldbmemoized_basedir(get_sdir())
  set_msgpackmemoized_basedir(get_sdir())



def get_basedir_file(filename):
  return get_basedir() + '/' + filename

def jsonload_basedir_file(filename):
  return json.load(open(get_basedir_file(filename)))

def basedir_exists(filename):
  return path.exists(get_basedir_file(filename))


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
  if basedir_exists('surveyresults.json'):
    return jsonload_basedir_file('surveyresults.json')
  return jsonload_basedir_file('testresults.json')

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


def get_fraction_correct_for_user(user):
  data = get_survey_results_for_user(user)
  correct = data['num_correct']
  total = data['num_total']
  return float(correct) / total

def get_taken_before_for_user(user):
  data = get_survey_results_for_user(user)
  return int(data['taken_before'] == 'yes')


def url_to_domain(url):
  return urlparse.urlparse(url).netloc

def print_counter(counter, **kwargs):
  num = kwargs.get('num', 100)
  keys_and_values = [{'key': k, 'val': v} for k,v in counter.viewitems()]
  keys_and_values.sort(key=itemgetter('val'), reverse=True)
  for item in keys_and_values[:num]:
    print item['key'], item['val']

def stringify_dict_sorted(counter):
  output = []
  #multiline = kwargs.get('multiline', True)
  for key in sorted(counter.viewkeys()):
    val = counter[key]
    output.append(str(key) + ': ' + str(val))
  return '{' + ', '.join(output) + '}'

def print_dict_sorted(counter):
  print stringify_dict_sorted(counter)

def print_yaml(val):
  print yaml.safe_dump(val)


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


@leveldbmemoized
def get_reconstructed_focus_times_for_user(user):
  ordered_visits = get_history_ordered_visits_for_user(user)
  reconstructor = ReconstructFocusTimesBaseline()
  for visit in ordered_visits:
    reconstructor.process_history_line(visit)
  return reconstructor.get_output()

@leveldbmemoized
def get_milliseconds_spent_on_domains_for_user(user):
  domain_to_timespent = Counter()
  for span in get_reconstructed_focus_times_for_user(user):
    url = span['url']
    domain = url_to_domain(url)
    duration = span['end'] - span['start']
    domain_to_timespent[domain] += duration
  return domain_to_timespent

@leveldbmemoized
def get_hours_spent_on_domains_for_user(user):
  return {k:v/(1000.0*3600) for k,v in get_milliseconds_spent_on_domains_for_user(user).items()}

@leveldbmemoized
def get_hours_spent_online_for_user(user):
  return sum(get_hours_spent_on_domains_for_user(user).values())


@memoized
def get_domain_to_category():
  return msgpack.load(open('rescuetime_categories/domain_to_category.msgpack'))

@memoized
def get_domain_to_productivity():
  return msgpack.load(open('rescuetime_categories/domain_to_productivity.msgpack'))

def domain_to_category(domain):
  return get_domain_to_category().get(domain, 'Uncategorized')

def domain_to_productivity(domain):
  return get_domain_to_productivity().get(domain, 0)

@memoized
def list_productivity_levels():
  return sorted(list(set(get_domain_to_productivity().values())))

@memoized
def list_categories():
  return sorted(list(set(get_domain_to_category().values())))


def get_hours_spent_on_domain_category_for_user(user):
  output = Counter()
  for domain,hours in get_hours_spent_on_domains_for_user(user).items():
    category = domain_to_category(domain)
    output[category] += hours
  return output

def get_hours_spent_on_domain_productivity_for_user(user):
  output = Counter()
  for domain,hours in get_hours_spent_on_domains_for_user(user).items():
    productivity = domain_to_productivity(domain)
    output[productivity] += hours
  return output


def get_hours_spent_productivity_neg2_for_user(user):
  data = get_hours_spent_on_domain_productivity_for_user(user)
  return data[-2]

def get_hours_spent_productivity_neg2or1_for_user(user):
  data = get_hours_spent_on_domain_productivity_for_user(user)
  return data[-2] + data[-1]

def get_hours_spent_productivity_pos2_for_user(user):
  data = get_hours_spent_on_domain_productivity_for_user(user)
  return data[2]

def get_hours_spent_productivity_pos2or1_for_user(user):
  data = get_hours_spent_on_domain_productivity_for_user(user)
  return data[2] + data[1]


def get_fraction_spent_productivity_neg2_for_user(user):
  data = get_hours_spent_on_domain_productivity_for_user(user)
  return data[-2] / float(sum(data.values()))

def get_fraction_spent_productivity_neg2or1_for_user(user):
  data = get_hours_spent_on_domain_productivity_for_user(user)
  return (data[-2] + data[-1]) / float(sum(data.values()))

def get_fraction_spent_productivity_pos2_for_user(user):
  data = get_hours_spent_on_domain_productivity_for_user(user)
  return data[2] / float(sum(data.values()))

def get_fraction_spent_productivity_pos2or1_for_user(user):
  data = get_hours_spent_on_domain_productivity_for_user(user)
  return (data[2] + data[1]) / float(sum(data.values()))


def get_hours_spent_social_networking_for_user(user):
  data = get_hours_spent_on_domain_category_for_user(user)
  return data['General Social Networking']

def get_fraction_spent_social_networking_for_user(user):
  data = get_hours_spent_on_domain_category_for_user(user)
  return data['General Social Networking'] / float(sum(data.values()))

