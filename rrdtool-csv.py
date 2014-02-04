#!/usr/bin/env python

"""A simple wrapper over `rrdtool fetch` to convert Munin data from rrd databases to csv format."""

import argparse
import csv
import json
import subprocess
import os
import re
import logging
import logging.handlers

from rrdtoolcsv import rrdtoolcsv_settings

logger = logging.getLogger()
logger.setLevel(logging.INFO)
syslog = logging.handlers.SysLogHandler(address='/dev/log')
formatter = logging.Formatter('RRDTOOL-CSV: %(levelname)s %(message)s')
syslog.setFormatter(formatter)
logger.addHandler(syslog)


def check_output(*popenargs, **kwargs):
    """ in case there is no subprocess.check_output function, define ours one. No such method prior python-2.7"""
    process = subprocess.Popen(stdout=subprocess.PIPE, *popenargs, **kwargs)
    output, unused_err = process.communicate()
    retcode = process.poll()
    if retcode:
        cmd = kwargs.get("args")
        if cmd is None:
            cmd = popenargs[0]
        error = subprocess.CalledProcessError(retcode, cmd)
        error.output = output
        raise error
    return output


def parse_args():
    """Parse command-line args"""
    parser = argparse.ArgumentParser(
        description='Converts data from RRD databases to CSV files.')
    parser.add_argument('-d', '--rrd_dir', type=str, default=rrdtoolcsv_settings.RRDIR,
                        help='Directory with .rrd files')
    parser.add_argument('-c', '--csv_file', type=str, default=rrdtoolcsv_settings.CSV_FILE,
                        help='.csv file to store results')
    parser.add_argument('-j', '--json_file', type=str, default=rrdtoolcsv_settings.JSON_FILE,
                        help='.json file with data filters')
    parser.add_argument('-r', '--resolution', type=int, default=rrdtoolcsv_settings.RESOLUTION,
                        help='fetch resolution in seconds')
    parser.add_argument('-s', '--start', type=str, default=rrdtoolcsv_settings.START,
                        help='start date in rrd fetch format')
    parser.add_argument('-e', '--end', type=str, default=rrdtoolcsv_settings.END,
                        help='end date in rrd fetch format')
    parser.add_argument('--daemon', type=str, default=rrdtoolcsv_settings.DAEMON,
                        help='rrdcached daemon')
    return parser.parse_args()


def run():
    """Execute the script"""
    args = parse_args()

    logger.info("args.resolution: %s \n" % args.resolution)
    logger.info("args.start: %s \n" % args.start)
    logger.info("args.end: %s \n" % args.end)

    rrdtool_output = {}
    files = files_to_read(args.json_file,args.rrd_dir)

    if not "check_output" in dir(subprocess):
        subprocess.check_output = check_output

    #Read rrd files with `rrdtool fetch` and store outputs in a dictionary
    for fname in files:
        file_path = os.path.join(args.rrd_dir, fname.name)

     #   use recorder last timestamp
     #   if str(args.start).lower() == "last" or str(args.start).lower() == 'l':
     #       try:
     #           lastfile = args.csv_file + ".timestamp"
     #           f = os.open(lastfile, os.O_RDONLY)
     #           timestamp = f.readline()
     #           args.start = timestamp
     #           os.close(f)
     #       except OSError:
     #           args.start = rrdtoolcsv_settings.START
     #           logger.critical("Cannot get lasttimestamp from %s for rrdtool file %s\n" %(lastfile, file_path))

        call = ['rrdtool', 'fetch', file_path, fname.aggregation,
                '-r', str(args.resolution),
                '-s', str(args.start), '-e', str(args.end)]
        if args.daemon:
            call.append(['--daemon',args.daemon])
        rrdtool_output[fname.machine+"#"+fname.get_alias()] = subprocess.check_output(call)

    #Merge results in a dictionary keyed by timestamps and dump them to csv file
    dump(merge(rrdtool_output), args.csv_file)

    # write last exported timestamp to args.csv_file.timestamp file
    #try:
    #    lastfile = args.csv_file + ".timestamp"
    #    f = os.open(lastfile, os.O_CREAT | os.O_WRONLY | os.O_EXCL)
    #    os.write(f, "%s\n" % lasttimestamp)
    #    os.close(f)
    #except OSError:
    #    logger.critical("Failed to save last exported timestamp to %s (rrdtool file %s)\n" %(lastfile,file_path))


def files_to_read(json_file, rrd_dir):
    """
    Return a list of file names to read and convert to CSV.
    The list is generated based on the parameters in settings file.

    @param str json_file: path to the file with data filters
    @param str rrd_dir: path to the directory with rrd files
    @return [MatchedFile]: list
    """
    file_pattern = re.compile(rrdtoolcsv_settings.FILE_FORMAT)
    all_files = os.listdir(rrd_dir)
    data = {}
    with open(json_file, 'r') as f:
        data = json.load(f)
    matched_files = []
    for file_name in all_files:
        match = file_matches(file_pattern, data, file_name)
        if match:
            matched_files.append(match)
    return matched_files


def file_matches(file_pattern, data, file_name):
    """
    Test whether a given file should be converted to csv.

    @param _sre.SRE_PATTERN file_pattern: regex to find matching files
    @param dict data: a dictionary with rules to match data, loaded from json file
    @param str,unicode file_name: file name to test
    @return MatchedFile if file should be processed, None otherwise
    """
    match = re.match(file_pattern, file_name)
    if match:
        matched_file = MatchedFile(file_name)
        matched_file.machine = match.group('machine')
        matched_file.chart = match.group('chart')
        matched_file.variable = match.group('variable')
        for machine in data['machines']:
            if machine['name'] == matched_file.machine:
                if 'aggregation' in machine:
                    matched_file.aggregation = machine['aggregation']
                for chart in machine['charts']:
                    if chart['name'] == matched_file.chart:
                        if 'aggregation' in chart:
                            matched_file.aggregation = chart['aggregation']
                        if not 'variables' in chart:
                            #If chart has no variables, we output all variables
                            return matched_file
                        else:
                            for variable in chart['variables']:
                                if variable['name'] == matched_file.variable:
                                    if 'aggregation' in variable:
                                        matched_file.aggregation = variable['aggregation']
                                    if 'alias' in variable:
                                        matched_file.alias = variable['alias']
                                    return matched_file
    return None


def merge(rrdtool_output):
    """
    Merge data from raw rrdtool output to a dictionary keyed by timestamp

    @param dict rrdtool_output: a dictionary contained results of fetching rrd data mapped by file alias
    @return dict result: dictionary of dictionaries containing merged rrd data mapped by timestamp.
     Each value is a dictionary mapping file alias to the value at given timestamp.
    """

    # sort full list by machine and timestamp
    def mysortkey(i):
        return str(i[0])+str(i[1])

    result = list()
    for combinedalias, output in rrdtool_output.iteritems():
        #Convert raw output to list of rows omitting empty rows
        machine, alias = combinedalias.split('#',1)
        rows = output.split('\n')[2:-1]

        #Parse rows and add values to the result
        for row in rows:
            split = row.split(': ', 1)
            timestamp = split[0]
            value = split[1].replace(',', '.')
            result.append([machine, timestamp, alias, value])

    result.sort(key=mysortkey)
    return result


def dump(merged_results, csv_file):
    """
    Dump results of merge function to csv file.
    @param dict merged_results: output of merge() function
    @param str csv_file: path to the file to write
    """

    #generate and write a header
    headers = ["machine", "timestamp", "metric", "value"]

    # write all rows from sorted result list
    with open(csv_file, 'wb') as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        for row in merged_results:
            writer.writerow(row)


class MatchedFile():

    def __init__(self, name):
        self.name = name
        self.machine = ''
        self.chart = ''
        self.variable = ''
        self.alias = ''
        self.aggregation = 'AVERAGE'

    def get_alias(self):
        if not self.alias:
            return self.chart+'_'+self.variable
        else:
            return self.alias

    def get_machine(self):
        return self.machine


if __name__ == '__main__':
    run()
