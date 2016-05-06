#!/usr/bin/env python
# md5: 76cf2d79138ebefa22dcbf0e12610def
# coding: utf-8

import plotly.offline as py
import plotly.graph_objs as go

py.init_notebook_mode()


def plot_histogram(vals):
  data = [
    go.Histogram(x=vals)
  ]
  py.iplot(data)

def plot_scatter(xvals, yvals):
  data = [
    go.Scatter(
      x=xvals,
      y=yvals,
      mode = 'markers'
    )
  ]
  py.iplot(data)


#plot_histogram([1, 1, 1, 2, 3, 4, 4, 4, 4, 5, 2, 2, 2, 2, 2, 2, 2])


#plot_scatter([1, 2, 3], [2, 6, 4])

