"""
start with:
> bokeh serve --allow-websocket-origin=127.0.0.1:5006 iplot.py --args path/to/filename.csv

opens csv and npy files, in case of npy, take "paramN.txt" in same folder as parameter names, seperator is whitespace or ";".
In case of csv, the first row will be parameter names, seperator is ";", give --sep SEPERATOR to change it
go to 127.0.0.1:5006 in your (modern) webbrowser ( 127.0.0.1:5006/iplot )

time is the number of observation, unless a label is named "timestamp" in which case this will be the time axis
optional additional python arguments all come after the --args path/to/filename:
 --sfile path/to/anotherfile.npy
  # You may load additional files which are appended to axis 1 of the first data. Give a --sfile option for each other file.
 --sep ","
  # Change the seperator for the loading of textfiles (default ";")
 --sep2 ","
  # Change the seperator for the loading of textfiles (reduced dimensionality) (default same as --sep)

packages required listed below:
"""
import sys
import os

import numpy as np

from bokeh.io import curdoc
from bokeh.layouts import row, column
from bokeh.models import ColumnDataSource
from bokeh.models.widgets import PreText, Select
from bokeh.plotting import figure

csv_seperator = ";"
if "--sep" in sys.argv:
	csv_seperator = sys.argv[sys.argv.index("--sep") + 1].strip('"').strip("'")
if "--sep2" in sys.argv:
	csv_seperator2 = sys.argv[sys.argv.index("--sep2") + 1].strip('"').strip("'")
else:
	csv_seperator2 = csv_seperator


### Load data ###
print("Opening file: %s"%sys.argv[1])
if sys.argv[1].split(".")[-1] == "npy":
	signal = np.load(sys.argv[1])
	n, p = signal.shape
	try:
		signalLabels = open(os.path.join(*(tuple(sys.argv[1].split(os.sep)[:-1]) + ("paramN.txt",)))).read().split()
		if len(signalLabels) == 1:
			signalLabels = signalLabels[0].split(";")
	except:
		signalLabels = ["%d"%i for i in range(p)]
else:
	signal = np.loadtxt(sys.argv[1], skiprows=1, delimiter=csv_seperator)
	n, p = signal.shape
	signalLabels = open(sys.argv[1]).readline().split(csv_seperator)
	signalLabels = [s.strip('"') for s in signalLabels]

if signalLabels[0] == "Timestamp" or signalLabels[0] == "timestamp":
	t = signal[:,0] - signal[0,0]
	signal = signal[:,1:]
	signalLabels = signalLabels[1:]
	p = p - 1
else:
	t = np.arange(len(signal))

if "--sfile" in sys.argv:
	i = 0
	k = -1
	while i < len(sys.argv):
		if sys.argv[i] == "--sfile":
			i += 1
			k += 1
			file = sys.argv[i]
			print("Opening additional file: %s"%file)
			if file.split(".")[-1] == "npy":
				signal2 = np.load(file)
				
			else:
				signal2 = np.loadtxt(file, skiprows=1, delimiter=csv_seperator)
				signalLabels2 = open(file).readline().split()
				if len(signalLabels2) == 1:
					signalLabels2 = signalLabels2[0].split(";")
			try:
				n2, p2 = signal2.shape
			except ValueError:
				n2, p2 = len(signal2), 1
				signal2 = np.reshape(signal2, [-1,1])
			if file.split(".")[-1] == "npy":
				if p2 == p:
					signalLabels2 = ["%s_2"%sl for sl in signalLabels]
				else:
					signalLabels2 = ["Extra_%d_%d"%(k, j) for j in range(p2)]
				
			signal = np.append(signal, signal2, axis=1)
			signalLabels = signalLabels + signalLabels2
			p = p + p2
		i += 1
		
if "--redux" in sys.argv:
	predux = True
	file = sys.argv[sys.argv.index("--redux") + 1]
	print("Opening file: %s as the reduced dimensionality space."%file)
	if file.split(".")[-1] == "npy":
		redux = np.load(file)
	else:
		redux = np.loadtxt(file, skiprows=0, delimiter=csv_seperator2)

	nr, pr = redux.shape
	signalLabels2 = ["Reduced_dim_%d"%i for i in range(pr)]
	
	signal = np.append(redux, signal, axis=1)
	signalLabels = signalLabels2 + signalLabels
	p = p + pr
else:
	predux = False
	
signalIndices = dict(zip(signalLabels, np.arange(len(signalLabels))))

def nix(val, lst):
	return [x for x in lst if x != val]

# set up widgets

stats = PreText(text='', width=400)
ticker1 = Select(value=signalLabels[0], options=nix(signalLabels[1], signalLabels))
ticker2 = Select(value=signalLabels[1], options=nix(signalLabels[0], signalLabels))

# set up plots

if predux:
	source = ColumnDataSource(data=dict(date=[], t1=[], t2=[], r1=[], r2=[]))
	source_static = ColumnDataSource(data=dict(date=[], t1=[], t2=[], r1=[], r2=[]))
else:
	source = ColumnDataSource(data=dict(date=[], t1=[], t2=[]))
	source_static = ColumnDataSource(data=dict(date=[], t1=[], t2=[]))

tools = 'pan,wheel_zoom,box_zoom,box_select,reset'

corr = figure(plot_width=400, plot_height=350,
              tools='pan,wheel_zoom,box_zoom,box_select,lasso_select,reset')
corr.circle('t1', 't2', size=2, source=source,
            selection_color="orange", alpha=0.6, nonselection_alpha=0.1, selection_alpha=0.4)

if predux:			
	reduced = figure(plot_width=400, plot_height=350,
				  tools='pan,wheel_zoom,box_zoom,box_select,lasso_select,reset')
	reduced.circle('r1', 'r2', size=2, source=source,
            selection_color="orange", alpha=0.6, nonselection_alpha=0.1, selection_alpha=0.4)

ts1 = figure(plot_width=1200, plot_height=250, tools=tools)
ts1.line('date', 't1', source=source_static)
ts1.circle('date', 't1', size=1, source=source, color=None, selection_color="orange")

ts2 = figure(plot_width=1200, plot_height=250, tools=tools)
ts2.x_range = ts1.x_range
ts2.line('date', 't2', source=source_static)
ts2.circle('date', 't2', size=1, source=source, color=None, selection_color="orange")

# set up callbacks

def ticker1_change(attrname, old, new):
	ticker2.options = nix(new, signalLabels)
	update()

def ticker2_change(attrname, old, new):
	ticker1.options = nix(new, signalLabels)
	update()

def update(selected=None):
	t1, t2 = ticker1.value, ticker2.value

	# data = get_data(t1, t2)
	# source.data = source.from_df(data[['t1', 't2']])
	data = dict(date=t, t1=signal[:,signalIndices[t1]], t2=signal[:,signalIndices[t2]])
	
	if predux:
		data['r1'] = redux[:,0]
		data['r2'] = redux[:,1]
	source.data = data
	source_static.data = source.data

	update_stats(data, t1, t2)

	corr.title.text = 'Scatter: %s vs. %s' % (t1, t2)
	if predux:
		reduced.title.text = 'Scatterplot reduced dimensionality'
	ts1.title.text, ts2.title.text = t1, t2

def statsText(data, t1, t2):
	space1 = 16
	space2 = 7
	text = "".ljust(space2) + t1.ljust(space1) + t2.ljust(space1) + '\n'
	text += "count".ljust(space2) + str(len(data["t1"])).ljust(space1) + str(len(data["t2"])).ljust(space1) + '\n'
	text += "mean".ljust(space2) + ("%.5g"%np.mean(data["t1"])).ljust(space1) + ("%.5g"%np.mean(data["t2"])).ljust(space1) + '\n'
	text += "std".ljust(space2) + ("%.5g"%np.std(data["t1"])).ljust(space1) + ("%.5g"%np.std(data["t2"])).ljust(space1) + '\n'
	text += "min".ljust(space2) + ("%.5g"%np.amin(data["t1"])).ljust(space1) + ("%.5g"%np.amin(data["t2"])).ljust(space1) + '\n'
	text += "max".ljust(space2) + ("%.5g"%np.amax(data["t1"])).ljust(space1) + ("%.5g"%np.amax(data["t2"])).ljust(space1) + '\n'
	
	return text
	
def update_stats(data, t1, t2):
	# stats.text = str(data[[t1, t2]].describe())
	stats.text = statsText(data, t1, t2)

ticker1.on_change('value', ticker1_change)
ticker2.on_change('value', ticker2_change)

def selection_change(attrname, old, new):
	t1, t2 = ticker1.value, ticker2.value
	selected = source.selected['1d']['indices']
	if selected:
		data = dict(date=t[selected], t1=signal[selected,signalIndices[t1]], t2=signal[selected,signalIndices[t2]])
	update_stats(data, t1, t2)

source.on_change('selected', selection_change)

# set up layout
widgets = column(ticker1, ticker2, stats)
main_row = row(corr, widgets, reduced) if predux else row(corr, widgets)
series = column(ts1, ts2)
layout = column(main_row, series)

# initialize
update()

curdoc().add_root(layout)
curdoc().title = sys.argv[1]