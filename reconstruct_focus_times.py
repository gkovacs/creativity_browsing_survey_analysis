#!/usr/bin/env python
# md5: 62a25a5731df0f7bf6c3aa8bd06207cc
# coding: utf-8

class ReconstructFocusTimesBaseline:
  def __init__(self):
    self.output = []
    self.curitem = {}
    self.idleperiod = 60*5 # seconds
    self.enabled_transitions = set([
      'link',
      'typed',
      'auto_bookmark',
      #'auto_subframe',
      #'manual_subframe',
      'generated',
      'auto_toplevel',
      'form_submit',
      'reload',
      'keyword',
      'keyword_generated',
    ])
  def get_output(self):
    self.end_input()
    return self.output
  def end_input(self):
    if 'url' in self.curitem:
      last_active = self.curitem['active']
      self.curitem['end_transition'] = 'end_input'
      self.curitem['end'] = last_active + self.idleperiod*1000
      self.output.append(self.curitem)
      self.curitem = {}
  def end_session(self, curtime, transition):
    if 'url' in self.curitem:
      last_active = self.curitem['active']
      # ensures that end < last_active+60 seconds
      self.curitem['end_transition'] = transition
      self.curitem['end'] = min(curtime, last_active + self.idleperiod*1000)
      #self.curitem['end'] = min(curtime, last_active + 1800*1000)
      self.output.append(self.curitem)
      self.curitem = {}
  def start_session(self, url, curtime, transition):
    if url == None:
      raise Exception('start_session should not be called with url==None')
    self.end_session(curtime, transition)
    # start: first event in the session
    # active: last event which was active in the session
    # end: when we believe the session ended
    self.curitem = {'url': url, 'start': curtime, 'active': curtime, 'transition': transition}
  def continue_session(self, url, curtime, transition):
    if url == None:
      raise Exception('continue_session should not be called with url==None')
    if 'url' not in self.curitem:
      self.start_session(url, curtime, transition)
      return
    prevurl = self.curitem['url']
    if url == prevurl: # still on same site
      # has it been less than 60 seconds since last activity?
      prev_active_time = self.curitem['active']
      if curtime < prev_active_time + self.idleperiod*1000:
        self.curitem['active'] = curtime
        return
    # have gone to different site
    self.end_session(curtime, transition)
    self.start_session(url, curtime, transition)
  def process_history_line(self, data):
    url = data['url']
    curtime = data['visitTime']
    transition = data['transition']
    if transition not in self.enabled_transitions:
      return
    self.continue_session(url, curtime, transition)

