vsc-monitoring
==============
Cluster monitoring tools

Functionality
-------------
* `plot_cluster_load_map.py`: creates a heat map representing the load
    of a cluster.  Each node is represented as a point, the color
    indicating the load (blue: not all cores busy, grey: all cores busy,
    red: cores oversubscribed), the size indicating the memory load
    (the larger the symbol, the more memory used on the node), the
    symbol indicates the node's state (circle: idle, square, single job,
    diamond: multiple jobs, cross: down).
* `plot_job_stats.py`: creates and updates a streaming plot of job
    statistics, i.e., the number of running, idle, system hold, deferred,
    batch hod, user hold, hold, and not queued jobs.
* `plot_queue_distribution.py`: creates a bar chart representing the
    number of running and queued jobs for each queue (q1h, q24h, q72h,
    q7d, q21d), and the corresponding number of nodes.

Plots are created on plot.ly (http://plot.ly/)

Dependencies
------------
* https://github.com/gjbex/vsc-tools-lib : it's lib directory
    shuold be in the PYTHONPATH variable.
* plotly Python package should be installed
* Python version 2.7.x required

