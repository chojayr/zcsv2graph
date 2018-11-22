#import numpy as np
import argparse
from numpy import genfromtxt
#from mpltools import style
import pandas as pd, sys
import matplotlib.pyplot as plt
import matplotlib.dates as md
import datetime as dt
import time
pd.__version__


SMALL_SIZE = 8
MED_SIZE = 10
BIG_SIZE = 18

plt.rc('font', size=SMALL_SIZE)          # controls default text sizes
plt.rc('axes', titlesize=BIG_SIZE)     # fontsize of the axes title
plt.rc('axes', labelsize=BIG_SIZE)    # fontsize of the x and y labels
plt.rc('xtick', labelsize=SMALL_SIZE)    # fontsize of the tick labels
plt.rc('ytick', labelsize=MED_SIZE)    # fontsize of the tick labels
plt.rc('legend', fontsize=MED_SIZE)    # legend fontsize

parser = argparse.ArgumentParser(description='convert csv files generated to graph')
parser.add_argument('-f', action='store', dest='csv_file', help='csv file generated from meter2csv.py script')
parser.add_argument('-g', '--graph', action='store', dest='metric', help='option: iops(read/write iops), mbps(read/write mbps), lats(read/write latency) or all') 
    
args = parser.parse_args()
csvf = args.csv_file


def rwIO(csvf):

  df1 = pd.read_csv(csvf, index_col=['date', 'time'], usecols=['dev_server_name', 'date', 'time', 'read.iops', 'write.iops'])
  dg = df1.groupby(['dev_server_name'])
  fig, ax = plt.subplots()
  tf1 = pd.read_csv(csvf)
  title = tf1['dev_ext_name'].iloc[0]
  labels = []
  for key, grp in dg:
    grp.plot(kind='line')
    plt.xlabel("Server: "+ grp['dev_server_name'].iloc[2])
    plt.grid(True, which='major', axis='both')
    fig.autofmt_xdate()
    plt.ylabel('ms')
    plt.title(title + " read/write iops")
    plt.legend()
    plt.gcf().set_size_inches(13, 7)
    ax.legend(labels)
    #save the graph into file
    plt.savefig(title + "_" + grp['dev_server_name'].iloc[2] + "_read&write_iops.png")

  #To show the graph uncomment below
  #plt.show()

def rwMBPS(csvf):

  df1 = pd.read_csv(csvf, index_col=["date", "time"], usecols=['dev_server_name', 'date', 'time', 'read.mbps', 'write.mbps'])
  dg = df1.groupby(['dev_server_name'])
  fig, ax = plt.subplots()
  tf1 = pd.read_csv(csvf)
  title = tf1['dev_ext_name'].iloc[0]
  labels = []
  for key, grp in dg:
    grp.plot(kind='line')
    plt.xlabel("Server: "+ grp['dev_server_name'].iloc[2])
    plt.grid(True, which='major', axis='both')
    fig.autofmt_xdate()
    plt.ylabel('mbps')
    plt.title(title + " read/write bandwidth(mbps)")
    plt.legend()
    plt.gcf().set_size_inches(13, 7)
    ax.legend(labels)
    #save the graph into file
    plt.savefig(title + "_" + grp['dev_server_name'].iloc[2] + "_read&write_mbps.png")

  #To show the graph uncomment below
  #plt.show()

def rwLatency(csvf):

  df1 = pd.read_csv(csvf, index_col=["date", "time"], usecols=['dev_server_name', 'date', 'time', 'read.latency_ms', 'write.latency_ms'])
  dg = df1.groupby(['dev_server_name'])
  fig, ax = plt.subplots()
  tf1 = pd.read_csv(csvf)
  title = tf1['dev_ext_name'].iloc[0]
  labels = []
  for key, grp in dg:
    grp.plot(kind='line')
    plt.xlabel("Server: "+ grp['dev_server_name'].iloc[2])
    plt.grid(True, which='major', axis='both')
    fig.autofmt_xdate()
    plt.ylabel('ms')
    plt.title(title + " read/write latency")
    plt.legend()
    plt.gcf().set_size_inches(13, 7)
    ax.legend(labels)
    #save the graph into file
    plt.savefig(title + "_" + grp['dev_server_name'].iloc[2] + "_read&write_latency.png")

  #To show the graph uncomment below
  #plt.show()

# Main
if args.metric == "iops":
  rwIO(csvf)
elif args.metric == "mbps":
  rwMBPS(csvf)
elif args.metric == "lats":
  rwLatency(csvf)
elif args.metric == "all":
  rwIO(csvf)
  rwMBPS(csvf)
  rwLatency(csvf)
else:
  print("please input the correct value(iops, mbps, lats or all)")
