#!/usr/bin/env python

from vsc.pbs.pbsnodes import PbsnodesParser


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


def compute_xy_labels(node_offset, nr_nodes, enclosures):
    n_min = node_offset
    n_max = n_min + nr_nodes
    x_labels = ['n{0:02d}'.format(i) for i in range(n_min, n_max)]
    y_labels = enclosures.split(',')
    return x_labels, y_labels


if __name__ == '__main__':
    from argparse import ArgumentParser
    import json
    import subprocess
    import sys

    arg_parser = ArgumentParser(description='Create a nodemap JSON file')
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
    arg_parser.add_argument('--node_map', help='node map file to use')
    arg_parser.add_argument('--verbose', action='store_true',
                            help='verbose output')
    options = arg_parser.parse_args()
    parser = PbsnodesParser()
    try:
        node_output = subprocess.check_output([options.pbsnodes])
        nodes = parser.parse(node_output)
    except subprocess.CalledProcessError:
        sys.stderr.write('### error: could not execute pbsnodes\n')
        sys.exit(1)
    x_labels, y_labels = compute_xy_labels(options.node_offset,
                                           options.nr_nodes,
                                           options.enclosures)
    x_coords, y_coords = compute_coordinates(x_labels, y_labels)
    names = [node.hostname for node in nodes
             if node.has_property(options.partition)]
    nodes = {}
    for name, x, y in zip(names, x_coords, y_coords):
        nodes[name] = [x, y]
    nodemap = {'x_labels': x_labels, 'y_labels': y_labels, 'nodes': nodes}
    with open(options.json, 'w') as json_file:
        json.dump(nodemap, json_file, indent=4)
