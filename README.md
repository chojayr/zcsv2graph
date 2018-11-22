# Create a graph from csv file using matplotlib

## The purpose of this script is to create a simple graph from the performance of the Zadara VPSA volume from the metering db dump. for you to able to use this you need to download first the metering db dump on the Zadara VPSA console, from System -> Settings -> Metering -> View 

## Then you need to use the meter2csv.py to convert the metering db data into csv and you can now use the script to create a graph from the generated csv file

## How to use meter2csv.py 

## python meter2csv.py db --localtime --dev_ext_name volume-0000007 >> file.csv

## then we can now use the data on file.csv to create the perfromance graph

## $ python csv2graph.py -f file.csv -g iops

## METRIC options

 * iops - read/write iops
 * mbps - read/write bandwidth
 * lats - read/write latency
 * all - provide all the image


