#
# Regular cron jobs for the musikernel1 package
#
0 4	* * *	root	[ -x /usr/bin/musikernel1_maintenance ] && /usr/bin/musikernel1_maintenance
