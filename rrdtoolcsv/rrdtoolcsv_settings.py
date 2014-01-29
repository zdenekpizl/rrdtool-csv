#Location of RRD files
#RRDIR = '/var/lib/munin/localdomain'
import os
import sys

RRDIR = '/home/zmicier/Downloads/rrd'

FILE_FORMAT = r'^(?P<machine>[\w.]+)-(?P<chart>[\w]+)-(?P<variable>[\w]+)-.\.rrd$'

CSV_FILE = '/tmp/rrdtool.csv'

JSON_FILE = os.path.join(sys.prefix,'rrdtool-csv','data.json')

#time resolution in seconds
RESOLUTION = 300

#Start of the time series to read. See http://oss.oetiker.ch/rrdtool/doc/rrdfetch.en.html for format options.
#If specifying as timestamp, it should be multiple of resolution
START = 'end-1day'

#End of the time series to read. See http://oss.oetiker.ch/rrdtool/doc/rrdfetch.en.html for format options.
#If specifying as timestamp, it should be multiple of resolution
END = 'now'

#Rrdcached daemon address to flush RRD files before reading them
DAEMON = ''