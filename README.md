#rrdtool-csv

A simple Python wrapper over `rrdtool fetch` to convert data from several round-robin database files into a single CSV file.

The script was written to convert data from the databases created with [Munin](http://munin-monitoring.org) monitoring tool. Thus, it assumes the files are named the way Munin does. If you want to use the script to convert data from other sources, you will have to adjust the way .rrd files are chosen for processing.

##Logic

The logic behind the script is the following. It is assumed we have a lot of .rrd files in a single directory that are named following this pattern: `machine.name-chart_name-variable_name-type.rrd`. Before running the script you have to write a small .json file that describes what data you want to retrieve. An example of such script can be found in `data` dir. You specify a list of machines to track, then for each of them you specify the charts and for each of the charts you specify the variables. If you do not specify any variables for the chart, all variables will be included in the output.

At all three levels (machine-chart-variable) you can specify a consolidation function (CF). CF at a finer level has precedence over the denser level. `AVERAGE` consolidation function is assumed by default.

For each variable you can specify its alias that will become a header of the respective column in a .csv file. By default, the alias is generated using chart name and variable name. 

When you launch the script, it fetches data from all the files found while processing the patterns in .json file and merges this data in a single table by timestamp. Then, this data is dumped to the specified .csv file.

##Command-line arguments
File-related:

* `-d` or `--rrd_dir` --- path to directory with .rrd files to parse 

* `-c` or `--csv_file` --- path to .csv file to store results
* `-j` or `--json_file` --- path to .json file with data filters

Rrdtool-related

* `-r` or `--resolution` --- resolution in seconds
* `-s` or `--start` --- start date in rrd fetch format
* `-e` or `--end` --- end date in rrd fetch format
* `--daemon` --- rrdcached daemon

Refer to [`rrdtool fetch` documentation](http://http://oss.oetiker.ch/rrdtool/doc/rrdfetch.en.html) for more detailed explanation on rrdtool-related parameters

Default values for all the parameters can be changed in `rrdtool_settings.py`

##Install
`python setup.py install`


