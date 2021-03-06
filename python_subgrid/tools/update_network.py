#!/usr/bin/env python

"""
Convert scriptlet, produce crosssection locations and definition
input from old network config
"""

# TODO:
# By default using naming convention of inp files:
# - ..net....inp
# - ..cros....inp
# - ..str....inp

# Change mdu file with new naming convention files

# Allow to use mdu file from any directory

# Script will be run like this:
# find . -name *.mdu -exec update-subgrid-network {} \;

import argparse
import datetime
import os
import sys

import numpy as np
import pandas

from python_subgrid.utils import MduParser
from python_subgrid.utils import MduParserKeepComments
from python_subgrid.utils import MultiSectionConfigParser


DEFAULTS = {
    'FrictType': '4',           # Default: Manning's formula for Chezy
    'FrictCoef': '0.026'        # Manning coefficient
}


def make_tables(nodes, definitions, branches):
    """
    process the content of the inp file into tables
    """

    # names as used in the files
    nodenames = ['id', 'type', 'x', 'y', 'depth', 'one']
    definitionnames = ['id', 'type', 'width']
    branchnames = ['id', 'type', 'from', 'to', 'c_from',
                   'c_to', 'npt', 'length']

    # combine all the records with the names
    tables = [nodes, definitions, branches]
    tablenames = [nodenames, definitionnames, branchnames]
    # create pandas dataframes so we can index by row and name
    dfs = []
    for table, names in zip(tables, tablenames):
        rows = []
        for record in table:
            if not record:
                continue
            # combine name and value, don't bother with type conversions
            row = dict(zip(names, record))
            rows.append(row)
        # create a data frame
        df = pandas.DataFrame(data=rows)
        dfs.append(df)
    return dfs


def merge_tables(nodesdf, definitionsdf, branchesdf):
    """
    combine branches and nodes tables into a crosssection table
    """

    # merge branches with the from nodes
    merged = branchesdf.merge(nodesdf,
                              left_on='from', right_on='id',
                              suffixes=('_branch', '_from'))
    # merge branches with the to nodes
    merged = merged.merge(nodesdf,
                          left_on='to', right_on='id',
                          suffixes=('_from', '_to'))

    # compute branch length
    merged['chainage'] = merged['length']
    # fill in missing with computed length
    idx = pandas.isnull(merged['chainage'])
    # compute length
    coords_from = np.asarray(merged[['x_from', 'y_from']], dtype='double')
    coords_to = np.array(merged[['x_to', 'y_to']], dtype='double')
    diffs = np.apply_along_axis(np.linalg.norm, 1, (coords_to - coords_from))
    merged['chainage'][idx] = diffs[idx]

    # Add the left and right cross section definition info
    cross_a = merged.merge(definitionsdf, left_on='c_from', right_on='id',
                           suffixes=['_c_from', '_cross'])
    cross_a['id'] = cross_a['id_branch'] + 'A'
    cross_a['chainage'] = 0
    cross_a['bottomlevel'] = -1*cross_a['depth_from'].astype('double')
    cross_b = merged.merge(definitionsdf, left_on='c_to', right_on='id',
                           suffixes=['_c_to', '_cross'])
    cross_b['id'] = cross_b['id_branch'] + 'B'
    cross_b['bottomlevel'] = -1*cross_b['depth_to'].astype('double')

    # combine the left and right tables
    crosssectionsdf = pandas.concat([cross_a, cross_b])
    crosssectionsdf = crosssectionsdf.rename(
        columns={'c_from': 'definition',
                 'id_branch': 'branchid'}
    )

    # Don't return everything, we only need this.
    columns = ['id', 'definition', 'branchid', 'chainage', 'bottomlevel']
    return crosssectionsdf[columns]


def parse_args():
    """
    Parse the command line arguments
    """
    argumentparser = argparse.ArgumentParser(
        description='Save grid and table administration.')
    argumentparser.add_argument('mdu', help='mdu files to process')
    argumentparser.add_argument('-n', '--network', dest='network',
                                help='new network file name',
                                default='one_d/network_MDUBASENAME.inp')
    argumentparser.add_argument('-c', '--crosssection',
                                dest="crosssection",
                                help='new crosssection file name',
                                default="one_d/crosssections_MDUBASENAME.inp")
    argumentparser.add_argument('-d', '--definition',
                                dest="definition",
                                help='new crosssection definition file name',
                                default="one_d/definitions_MDUBASENAME.inp")
    arguments = argumentparser.parse_args()
    # replace MDUBASENAME with basename
    for dest in ("network", "crosssection", "definition"):
        if argumentparser.get_default(dest) == getattr(arguments, dest):
            basename = os.path.basename(arguments.mdu)
            basename = os.path.splitext(basename)[0]
            filename = getattr(arguments, dest).replace("MDUBASENAME",
                                                        basename)
            setattr(arguments,
                    dest,
                    filename)

    return arguments


def main():
    """main program"""
    arguments = parse_args()

    # Read mdu file
    mdudir = os.path.dirname(arguments.mdu)
    mduparser = MduParser(defaults=DEFAULTS)
    mduparser.readfp(open(arguments.mdu))
    networkfilename = mduparser.get('geometry', 'NetworkFile')

    # Split up the old network file
    lines = open(os.path.join(mdudir, networkfilename)).readlines()
    records = [line.split() for line in lines]
    breaks = [i for i, record in enumerate(records) if record == ['-1']]
    nodes, definitions, branches = (records[:breaks[0]],
                                    records[breaks[0]+1:breaks[1]],
                                    records[breaks[1]+1:])
    # Create tables
    (nodesdf,
     definitionsdf,
     branchesdf) = make_tables(nodes, definitions, branches)
    # Merge them
    crosssectionsdf = merge_tables(nodesdf,
                                   definitionsdf,
                                   branchesdf)

    # Some manual changes

    # rectangles all the way down
    definitionsdf["type"] = "rectangle"

    # Add some friction
    frictcoef = mduparser.getfloat('physics', 'FrictCoef')
    fricttype = mduparser.getint('physics', 'FrictType')
    crosssectionsdf['frictiontype'] = fricttype
    crosssectionsdf['frictionvalue'] = frictcoef

    # Write out the definitions
    config = MultiSectionConfigParser()
    for i, definition in definitionsdf.iterrows():
        config.add_section('Definition')
        for key, value in definition.iteritems():
            config.set('Definition', key, str(value))
    with open(os.path.join(mdudir, arguments.definition), 'w') as f:
        config.write(f)

    # and write the crosssections
    config = MultiSectionConfigParser()
    for i, crosssection in crosssectionsdf.sort('id').iterrows():
        config.add_section('CrossSection')
        for key, value in crosssection.iteritems():
            config.set('CrossSection', key, str(value))
    with open(os.path.join(mdudir, arguments.crosssection), 'w') as f:
        config.write(f)

    # and write the network
    lines = []
    for i, node in nodesdf.iterrows():
        lines.append("{id} {type} {x} {y}".format(**node))
    lines.append("-1")
    for i, branch in branchesdf.iterrows():
        if int(branch['type']) == 0:
            lines.append("{id} {type} {from} {to}".format(**branch))
        else:
            lines.append("{id} {type} {from} {to} {npt}".format(**branch))
    with open(arguments.network, 'w') as networkfile:
        networkfile.writelines(line + "\n" for line in lines)

    commentedmdu = MduParserKeepComments()
    commentedmdu.readfp(open(arguments.mdu))
    commentedmdu.set("geometry",
                     "CrossSectionFile",
                     arguments.crosssection)
    commentedmdu.set("geometry",
                     "CrossSectionDefinitionFile",
                     arguments.definition)
    with open(arguments.mdu, 'w') as mdufile:
        comment = "# mdu file changed by {} at {}".format(
            sys.argv[0],
            datetime.datetime.now()
        )
        mdufile.write(comment + "\n")
        commentedmdu.write(mdufile)


if __name__ == "__main__":
    main()
