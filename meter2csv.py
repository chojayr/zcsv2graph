#!/usr/bin/env python

import argparse
import sqlite3
import csv
import sys

# @see common/tools/zmeter.h::zmeter_device_type_t
dev_types = {'FE': 1, 'RG': 2, 'BE': 3, 'POOL': 4, 'SYSTEM': 5, 'MIRROR': 6, 'ZCACHE': 7, 'BLOCK': 10, 'NOVA': 11, 'MIGR': 13, 'OBJ': 14, 'DOCKER': 15, 'NETDEV': 16, 'CONTAINER': 17}

parser = argparse.ArgumentParser(description='Convert metering database into CSV')
parser.add_argument('db', help='metering DB')
parser.add_argument('-z', action='store_true', help='omit records with no I/O activity.')
parser.add_argument('-v', '--verbose', action='store_true')
parser.add_argument('-x', '--extended', action='store_true', help='output non-rw stats')
parser.add_argument('--localtime', action='store_true', help='output times in localtime (default UTC)')
flt_group = parser.add_argument_group('Filters')
flt_group.add_argument('--dev_dbid', type=int, help='filter output by device dbid')
flt_group.add_argument('--dev_type', choices=dev_types.keys(), help='filter output by device type')
flt_group.add_argument('--dev_ext_name', help='filter output by internal device name')
flt_group.add_argument('--dev_server_name', help='filter output by internal server name, for BE devices USER/SETUP mean user/setup partitions')
flt_group.add_argument('--dev_target_name', help='filter output by target name')
flt_group.add_argument('--unixtime', type=int, help='filter output by metering time (secs from Jan 1, 1970)')

args = parser.parse_args()

if args.dev_type == 'SYSTEM':
	dev_type_str = 'system'
elif args.dev_type == 'DOCKER':
	dev_type_str = 'docker'
elif args.dev_type == 'CONTAINER':
	dev_type_str = 'container'
elif args.dev_type == 'ZCACHE':
	dev_type_str = 'zcache'
elif args.dev_type == 'NETDEV':
	dev_type_str = 'netdev'
else:
	dev_type_str = 'io'

conn = sqlite3.connect(args.db)
cursor = conn.cursor()

common_fieldnames = ['dev_dbid', 'dev_type', 'dev_ext_name', 'dev_server_name', 'dev_target_name', 'unixtime', 'date', 'time', 'interval']
fieldnames = list(common_fieldnames)

# Prepare SELECT statements
if dev_type_str == 'io':
	if args.dev_type is None:
		query = 'SELECT dev_type, bucket, bucket_name FROM io_buckets'
	else:
		query = 'SELECT dev_type, bucket, bucket_name FROM io_buckets WHERE dev_type = {}'.format(dev_types[args.dev_type])
	if args.verbose:
		print >> sys.stderr, 'Load io buckets'
		print >> sys.stderr, query
	cursor.execute(query + ';')

	io_buckets = dict()
	bucket_names = list()
	for sql_row in cursor:
		dev_type = sql_row[0]
		bucket = sql_row[1]
		bucket_name = sql_row[2]
		if args.extended or (bucket_name.lower()=='read' or bucket_name.lower()=='write'):
			io_buckets[(dev_type, bucket)] = bucket_name
			if bucket_name not in bucket_names:
				bucket_names.append(bucket_name)

	table = 'metering_info'
	fields = 'bucket, '																+ \
			'ROUND( CAST(num_ios AS REAL) / interval, 3) AS iops, '					+ \
			'active_ios, io_errors, '												+ \
			'ROUND( (CAST(bytes AS REAL) / interval) / (1024*1024), 3) AS mbps, '	+ \
			'ROUND( CAST(total_resp_tm_ms AS REAL) / num_ios, 3) AS latency_ms, '	+ \
			'max_resp_tm_ms AS max_latency_ms, max_cmd '
	for bucket_name in bucket_names:
		fieldnames.append(bucket_name + '.iops')
		fieldnames.append(bucket_name + '.active_ios')
		fieldnames.append(bucket_name + '.io_errors')
		fieldnames.append(bucket_name + '.mbps')
		fieldnames.append(bucket_name + '.latency_ms')
		fieldnames.append(bucket_name + '.max_latency_ms')
		fieldnames.append(bucket_name + '.max_cmd')
elif dev_type_str == 'system' or dev_type_str == 'docker' or dev_type_str == 'container':
	table = 'metering_sys_info'
	fields = 'ROUND(CAST(100.0 * cpu_user AS REAL) / (cpu_user + cpu_system + cpu_iowait + cpu_idle), 3) AS cpu_user, '		+ \
			'ROUND(CAST(100.0 * cpu_system AS REAL) / (cpu_user + cpu_system + cpu_iowait + cpu_idle), 3) AS cpu_system, '	+ \
			'ROUND(CAST(100.0 * cpu_iowait AS REAL) / (cpu_user + cpu_system + cpu_iowait + cpu_idle), 3) AS cpu_iowait, '	+ \
			'ROUND(CAST(100.0 * cpu_idle AS REAL) / (cpu_user + cpu_system + cpu_iowait + cpu_idle), 3) AS cpu_idle, '		+ \
			'memory AS mem_used, mem_alloc, mem_active '
	fieldnames.append('cpu_user')
	fieldnames.append('cpu_system')
	fieldnames.append('cpu_iowait')
	fieldnames.append('cpu_idle')
	fieldnames.append('mem_used')
	fieldnames.append('mem_alloc')
	fieldnames.append('mem_active')
elif dev_type_str == 'zcache':
	table = 'metering_zcache_info'
	fields = 'data_dirty, meta_dirty, data_clean, meta_clean, data_cb_util, meta_cb_util, ' + \
			'data_read_hit, meta_read_hit, data_write_hit, meta_write_hit '
	fieldnames.append('data_dirty')
	fieldnames.append('meta_dirty')
	fieldnames.append('data_clean')
	fieldnames.append('meta_clean')
	fieldnames.append('data_cb_util')
	fieldnames.append('meta_cb_util')
	fieldnames.append('data_read_hit')
	fieldnames.append('meta_read_hit')
	fieldnames.append('data_write_hit')
	fieldnames.append('meta_write_hit')
#dev_type_str = netdev
else:
	table = 'metering_netdev_info'
	fields = 'rx_packets, rx_bytes, rx_errors, rx_dropped, tx_packets, tx_bytes, tx_errors, tx_dropped '
	fieldnames.append('rx_packets')
	fieldnames.append('rx_bytes')
	fieldnames.append('rx_errors')
	fieldnames.append('rx_dropped')
	fieldnames.append('tx_packets')
	fieldnames.append('tx_bytes')
	fieldnames.append('tx_errors')
	fieldnames.append('tx_dropped')
 
# Prepara WHERE statements
where = "1 "
if args.z:
	if table == 'metering_info':
		where += "AND num_ios != 0 "
	else:
		where += "AND (cpu_user != 0 or cpu_system != 0) "
if args.dev_dbid is not None:
	where += "AND {}.dev_dbid = {} ".format(table, args.dev_dbid)
if args.dev_type is not None:
	where += "AND dev_type = {0} ".format(dev_types[args.dev_type])
if args.dev_ext_name is not None:
	if args.dev_ext_name != "":
		where += "AND dev_ext_name = '{0}' ".format(str(args.dev_ext_name))
	else:
		where += "AND dev_ext_name is NULL "
if args.dev_server_name is not None:
	if args.dev_server_name != "":
		where += "AND dev_server_name = '{0}' ".format(str(args.dev_server_name))
	else:
		where += "AND dev_server_name is NULL "
if args.dev_target_name is not None:
	if args.dev_target_name != "":
		where += "AND dev_target_name = '{0}' ".format(str(args.dev_target_name))
	else:
		where += "AND dev_target_name is NULL "
if args.unixtime is not None:
	where += "AND unixtime = {0} ".format(str(args.unixtime))



# http://www.sqlite.org/lang_datefunc.html
wanttime = "'unixepoch'"
if args.localtime:
	wanttime = "'unixepoch', 'localtime'"

# Build the query
query = 'SELECT devices.dev_dbid, dev_type, dev_ext_name, dev_server_name, dev_target_name, '	+ \
		'time AS unixtime, '																	+ \
		'DATE(time, ' + wanttime + ') AS date, '												+ \
		'TIME(time, ' + wanttime + ') AS time, '												+ \
		'interval, ' + fields + ' '																+ \
		'FROM (devices JOIN {0} ON devices.dev_dbid = {0}.dev_dbid) '.format(table)				+ \
		'WHERE ' + where + ' '																	+ \
		'ORDER BY dev_type, dev_ext_name, dev_server_name, dev_target_name, {0}.time '.format(table)

if args.verbose:
	print >> sys.stderr, 'Execute main query'
	print >> sys.stderr, query
cursor.execute(query + ';')

if args.verbose:
	print >> sys.stderr, 'Store as .csv'

# Store recordsets in csv format
csv.register_dialect('excel_n', lineterminator='\n')
writer = csv.DictWriter(sys.stdout, fieldnames, dialect='excel_n')

header = dict()
for f in fieldnames:
	header[f] = f
writer.writerow(header)

common_fieldnames_cnt = len(common_fieldnames)

csv_row = dict()
prev_sql_row = list()
for sql_row in cursor:

	if prev_sql_row[0:common_fieldnames_cnt] != sql_row[0:common_fieldnames_cnt]:
		if len(csv_row) > 0:
			writer.writerow(csv_row)
			csv_row.clear()
		for i in range(0, common_fieldnames_cnt):
			fname = common_fieldnames[i]
			csv_row[fname] = sql_row[i]
		dev_type_id = csv_row['dev_type']

	for dt in dev_types.items():
		if dev_type_id == dt[1]:
			csv_row['dev_type'] = dt[0]

	if dev_type_str == 'io':
		bucket_id = sql_row[common_fieldnames_cnt+0]
		bucket_name = io_buckets.get((dev_type_id, bucket_id))
		if bucket_name is not None:
			csv_row[bucket_name + '.iops'] = sql_row[common_fieldnames_cnt+1]
			csv_row[bucket_name + '.active_ios'] = sql_row[common_fieldnames_cnt+2]
			csv_row[bucket_name + '.io_errors'] = sql_row[common_fieldnames_cnt+3]
			csv_row[bucket_name + '.mbps'] = sql_row[common_fieldnames_cnt+4]
			csv_row[bucket_name + '.latency_ms'] = sql_row[common_fieldnames_cnt+5]
			csv_row[bucket_name + '.max_latency_ms'] = sql_row[common_fieldnames_cnt+6]
			csv_row[bucket_name + '.max_cmd'] = sql_row[common_fieldnames_cnt+7]
	elif dev_type_str == 'system':
		csv_row['cpu_user'] = sql_row[common_fieldnames_cnt+0]
		csv_row['cpu_system'] = sql_row[common_fieldnames_cnt+1]
		csv_row['cpu_iowait'] = sql_row[common_fieldnames_cnt+2]
		csv_row['cpu_idle'] = sql_row[common_fieldnames_cnt+3]
		csv_row['mem_used'] = sql_row[common_fieldnames_cnt+4]
		csv_row['mem_alloc'] = sql_row[common_fieldnames_cnt+5]
		csv_row['mem_active'] = sql_row[common_fieldnames_cnt+6]
	elif dev_type_str == 'zcache':
		csv_row['data_dirty'] = sql_row[common_fieldnames_cnt+0]
		csv_row['meta_dirty'] = sql_row[common_fieldnames_cnt+1]
		csv_row['data_clean'] = sql_row[common_fieldnames_cnt+2]
		csv_row['meta_clean'] = sql_row[common_fieldnames_cnt+3]
		csv_row['data_cb_util'] = sql_row[common_fieldnames_cnt+4]
		csv_row['meta_cb_util'] = sql_row[common_fieldnames_cnt+5]
		csv_row['data_read_hit'] = sql_row[common_fieldnames_cnt+6]
		csv_row['meta_read_hit'] = sql_row[common_fieldnames_cnt+7]
		csv_row['data_write_hit'] = sql_row[common_fieldnames_cnt+8]
		csv_row['meta_write_hit'] = sql_row[common_fieldnames_cnt+9]
#dev_type_str = netdev
	else:
		csv_row['rx_packets'] = sql_row[common_fieldnames_cnt+0]
		csv_row['rx_bytes'] = sql_row[common_fieldnames_cnt+1]
		csv_row['rx_errors'] = sql_row[common_fieldnames_cnt+2]
		csv_row['rx_dropped'] = sql_row[common_fieldnames_cnt+3]
		csv_row['tx_packets'] = sql_row[common_fieldnames_cnt+4]
		csv_row['tx_bytes'] = sql_row[common_fieldnames_cnt+5]
		csv_row['tx_errors'] = sql_row[common_fieldnames_cnt+6]
		csv_row['tx_dropped'] = sql_row[common_fieldnames_cnt+7]

	prev_sql_row = sql_row

# Write last row
writer.writerow(csv_row)
