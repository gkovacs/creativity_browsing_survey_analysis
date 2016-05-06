#!/usr/bin/env python
# md5: c8c7e2dc9266b7657d2d6f82057abf8d
# coding: utf-8

from analysis_base import *
from plot_utils import *
from scipy.stats import pearsonr


def is_user_blacklisted(user):
  if user in ['jess', 'geza', 'shivaal', 'gezaeducrowdtest']:
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
  print {'r': r, 'r^2': r**2, 'p': p}
  plot_scatter_for_func_pair(func1, func2)

def print_results_for_func_pair(func1, func2):
  for x in list_allowed_users():
    print x, func1(x), func2(x)


#func_correlation(get_fraction_correct_for_user, get_hours_spent_online_for_user)

