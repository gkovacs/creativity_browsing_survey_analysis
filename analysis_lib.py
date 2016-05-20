#!/usr/bin/env python
# md5: af317caae95cb7406fd0ecaf1faaec0b
# coding: utf-8

from analysis_base import *
from plot_utils import *
from scipy.stats import pearsonr


def is_user_blacklisted(user):
  if user in ['jess', 'geza', 'shivaal', 'gezaeducrowdtest', 'A1VL7507UONPX0', 'A207IHY6GERCFO']: # browsingsurvey
    return True
  if user in ['A1XH05IKC77OXO', 'A1GRL544SI7RTG']: # browsingsurvey2
    return True
  if user.startswith('guest'):
    return True
  return False

@memoized
def list_allowed_users():
  return [x for x in list_users() if not is_user_blacklisted(x)]

def plot_histogram_for_func(func):
  plot_histogram([func(x) for x in list_allowed_users()])

def print_results_for_func(func):
  for x in list_allowed_users():
    print x, func(x)

def plot_scatter_for_func_pair(func1, func2):
  xdata = [func1(x) for x in list_allowed_users()]
  ydata = [func2(x) for x in list_allowed_users()]
  plot_scatter(xdata, ydata)

def func_correlation(func1, func2):
  xdata = [func1(x) for x in list_allowed_users()]
  ydata = [func2(x) for x in list_allowed_users()]
  r,p = pearsonr(xdata, ydata)
  print_dict_sorted({'r': r, 'r^2': r**2, 'p': p})
  plot_scatter_for_func_pair(func1, func2)

def print_results_for_func_pair(func1, func2):
  for x in list_allowed_users():
    print x, func1(x), func2(x)


#func_correlation(get_fraction_correct_for_user, get_hours_spent_online_for_user)

