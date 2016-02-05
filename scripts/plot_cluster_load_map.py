#!/usr/bin/env python

import subprocess
import plotly.plotly as py
from plotly.graph_objs import Data, Layout, Figure, Scatter, Marker
from vsc.pbs.pbsnodes import PbsnodesParser
from vsc.plotly_utils import create_annotations, sign_in


DEFAULT_ENCLOSURES = ('r1i0,r1i1,r1i2,r2i0,r2i1,r2i2,r3i0,r3i1,'
                      'r3i2,r4i0,r4i1,r5i0,r5i1,r4i2,r5i2,r8i0')


def compute_coordinates(x, y):
    x_coords = []
    y_coords = []
    for j in xrange(1, 1 + len(y)):
        for i in xrange(1, 1 + len(x)):
            x_coords.append(i)
            y_coords.append(j)
    return x_coords, y_coords


def compute_cpu_colors(cpu):
    nr_blues = 7
    color_map = [
        'rgb(37,0,250)',
        'rgb(57,28,250)',
        'rgb(79,52,250)',
        'rgb(107,85,250)',
        'rgb(138,119,250)',
        'rgb(164,150,250)',
        'rgb(200,200,200)',  # grey
        'rgb(250,177,177)',
        'rgb(250,93,93)',
        'rgb(250,0,0)',
    ]
    down_color = 'rgb(0,0,0)'
    colors = []
    for cpu_value in cpu:
        if cpu_value < -0.1:
            colors.append(down_color)
        else:
            if cpu_value <= 1.01:
                idx = int(round((nr_blues - 1)*cpu_value))
            elif cpu_value <= 1.06:
                idx = nr_blues
            elif cpu_value <= 2.0:
                idx = nr_blues + 1
            else:
                idx = nr_blues + 2
            colors.append(color_map[idx])
    return colors


def compute_mem_sizes(mem):
    sizes = []
    down_size = 10
    for mem_value in mem:
        if mem_value < -0.1:
            sizes.append(down_size)
        else:
            size = 15 + 20*mem_value
            sizes.append(size)
    return sizes


def compute_status_symbols(status):
    symbol_map = {
        'free': 'circle',
        'down': 'cross',
        'singlejob': 'square',
        'multijob': 'diamond',
    }
    symbols = []
    for state in status:
        if state.startswith('donw') or state.startswith('offline'):
            symbols.append(symbol_map['down'])
        else:
            symbols.append(symbol_map[state])
    return symbols


def compute_texts(names, cpu, mem, status, jobs):
    texts = []
    for idx in xrange(len(names)):
        text_str = '<b>{0}</b>'.format(names[idx])
        if not (status[idx].startswith('down') or
                status[idx].startswith('offline')):
            text_str += '<br>CPU: {0:.2f}'.format(cpu[idx])
            text_str += '<br>MEM: {0:.2f}'.format(mem[idx])
            if status[idx] != 'free':
                text_str += '<br>JOB: {0}'.format(','.join(jobs[idx]))
        else:
            text_str += ' DOWN'
        texts.append(text_str)
    return texts


def collect_coordinates(names, node_map):
    x_coords = []
    y_coords = []
    for name in names:
        x = int(node_map['nodes'][name][0])
        y = int(node_map['nodes'][name][1])
        x_coords.append(x)
        y_coords.append(y)
    return x_coords, y_coords


def create_figure(names, cpu, mem, status, jobs, x, y,
                  partition='thinking', node_map=None):
    if node_map:
        x_coords, y_coords = collect_coordinates(names, node_map)
    else:
        x_coords, y_coords = compute_coordinates(x, y)
    cpu_colors = compute_cpu_colors(cpu)
    mem_sizes = compute_mem_sizes(mem)
    status_symbols = compute_status_symbols(status)
    texts = compute_texts(names, cpu, mem, status, jobs)
    trace = Scatter(
        x=x_coords, y=y_coords, mode='markers',
        marker=Marker(
            color=cpu_colors,
            size=mem_sizes,
            symbol=status_symbols,
        ),
        text=texts,
    )
    data = Data([trace])
    layout = Layout(
        title='{0} load'.format(partition),
        showlegend=False,
        annotations=create_annotations(),
        xaxis={'autotick': False, 'tickmode': 'array',
               'tickvals': range(1, len(x) + 1), 'ticktext': x},
        yaxis={'autotick': False, 'tickmode': 'array',
               'tickvals': range(1, len(y) + 1), 'ticktext': y},
        width=950,
        height=800,
        hovermode='closest',
    )
    return Figure(data=data, layout=layout)


def create_plot(names, cpu, mem, status, jobs, x, y, options,
                node_map=None):
    figure = create_figure(names, cpu, mem, status, jobs, x, y,
                           options.partition, node_map)
    filename = '{0}_cpu_load'.format(options.partition)
    if options.dryrun:
        return 'dryrun'
    else:
        url = py.plot(figure, filename=filename, auto_open=False)
        return url


def compute_maps(nodes, names):
    cpu = []
    mem = []
    for node in (n for n in nodes if n.hostname in names):
        cpu.append(node.cpuload if node.cpuload is not None else -1.0)
        mem.append(node.memload if node.memload is not None else -1.0)
    return cpu, mem


def compute_job_status(nodes, names):
    jobs = []
    status = []
    for node in (n for n in nodes if n.hostname in names):
        if node.status:
            if node.job_ids:
                jobs.append(node.job_ids)
                if len(node.job_ids) > 1:
                    status.append('multijob')
                else:
                    status.append('singlejob')
            elif (node.state.startswith('down') or
                  node.state.startswith('offline')):
                jobs.append([])
                status.append('down')
            else:
                jobs.append([])
                status.append('free')
        else:
            jobs.append(None)
            status.append('down')
    return jobs, status


def compute_xy_labels(node_offset, nr_nodes, enclosures):
    n_min = node_offset
    n_max = n_min + nr_nodes
    x_labels = ['n{0:02d}'.format(i) for i in range(n_min, n_max)]
    y_labels = enclosures.split(',')
    return x_labels, y_labels


def create_map(pbsnodes, node_map, partition='thinking'):
    parser = PbsnodesParser()
    node_output = subprocess.check_output([pbsnodes])
    nodes = parser.parse(node_output)
    x_labels = node_map['x_labels']
    y_labels = node_map['y_labels']
    names = node_map['nodes'].keys()
    cpu, mem = compute_maps(nodes, names)
    jobs, status = compute_job_status(nodes, names)
    return create_figure(names, cpu, mem, status, jobs,
                         x_labels, y_labels, partition, node_map)


if __name__ == '__main__':
    from argparse import ArgumentParser
    import json
    import sys

    arg_parser = ArgumentParser(description='Create a heatmap of CPU load')
    arg_parser.add_argument('--partition', default='thinking',
                            help='cluster partition to visualize')
    arg_parser.add_argument('--enclosures', default='r1i0,r1i1,r1i2,r2i0,'
                                                    'r2i1,r2i2,r3i0,r3i1,'
                                                    'r3i2,r4i0,r4i1,r5i0,'
                                                    'r5i1,r4i2,r5i2,r8i0',
                            help='list of enclosures')
    arg_parser.add_argument('--nr_nodes', type=int, default=16,
                            help='number of nodes per IRU')
    arg_parser.add_argument('--node_offset', type=int, default=1,
                            help='node offset')
    arg_parser.add_argument('--pbsnodes', default='/usr/local/bin/pbsnodes',
                            help='pbsnodes command to use')
    arg_parser.add_argument('--conf', default='~/.plotly/plotly.conf',
                            help='configuration file to use')
    arg_parser.add_argument('--node_map', help='node map file to use')
    arg_parser.add_argument('--verbose', action='store_true',
                            help='verbose output')
    arg_parser.add_argument('--dryrun', action='store_true',
                            help='do not create plot')
    arg_parser.add_argument('--file', help='file with pbsnodes output')
    options = arg_parser.parse_args()
    sign_in(options.conf)
    if options.node_map:
        with open(options.node_map, 'r') as node_map_file:
            node_map = json.load(node_map_file)
    else:
        node_map = None
    parser = PbsnodesParser()
    if options.file:
        with open(options.file, 'r') as pbs_file:
            nodes = parser.parse_file(pbs_file)
    else:
        try:
            node_output = subprocess.check_output([options.pbsnodes])
            nodes = parser.parse(node_output)
        except subprocess.CalledProcessError:
            sys.stderr.write('### error: could not execute pbsnodes\n')
            sys.exit(1)
    if options.verbose:
        print '{0:d} nodes found'.format(len(nodes))
    if options.node_map:
        x_labels = node_map['x_labels']
        y_labels = node_map['y_labels']
    else:
        x_labels, y_labels = compute_xy_labels(options.node_offset,
                                               options.nr_nodes,
                                               options.enclosures)
    if options.verbose:
        print '{0:d} x-labels, {1:d} y-labels'.format(len(x_labels),
                                                      len(y_labels))
    if options.node_map:
        names = node_map['nodes'].keys()
    else:
        names = [node.hostname for node in nodes
                 if node.has_property(options.partition)]
    if options.verbose:
        print 'names:'
        print '\n'.join(names)
    cpu, mem = compute_maps(nodes, names)
    jobs, status = compute_job_status(nodes, names)
    url = create_plot(names, cpu, mem, status, jobs,
                      x_labels, y_labels, options, node_map)
    print 'URL: {0}'.format(url)
