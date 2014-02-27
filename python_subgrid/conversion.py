"""
Convert scriptlets
* convert_subgrid_mdu: translate an old formatted MDU file (version < 2) to the new v2.1 structure.
"""

import os
import argparse
import sys
import datetime

import numpy as np

from python_subgrid.utils import MduParser, MduParserKeepComments, MultiSectionConfigParser


def parse_args():
    """
    Parse the command line arguments
    """
    argumentparser = argparse.ArgumentParser(
        description='Convert an old MDU (version < 2) to the new structure.')
    argumentparser.add_argument('mdu', help='mdu files to process')
    arguments = argumentparser.parse_args()

    return arguments

########################
# TODO: move to utils?
def rename_section(config, section1, section2):
    """rename section1 to section2 in the config object"""

    # lookup all items in section1
    items = config.items(section1)
    # add section 2
    config.add_section(section2)
    # copy all items from section1 to section2
    for option, value in items:
        config.set(section2, option, value)
    config.remove_section(section1)


# TODO: move to utils?
def opt_rename(config, section1, section2, option1, option2):
    """rename section1, option1  to section2, option2 """
    try:
        config.set(section2, option2, config.get(section1, option1, 1))
    except ConfigParser.NoSectionError:
        # Create non-existent section
        config.add_section(section2)
        opt_rename(config, section1, section2, option1, option2)
    else:
        config.remove_option(section1, option1)

########################

# 
# Allow to use mdu file from any directory
# Script will be run like this:
# find . -name *.mdu -exec update-subgrid-mdu {} \;
def convert_subgrid_mdu():
    """Change mdu file to new version >=2.0 MDU File Format"""
    arguments = parse_args()

    # Read mdu file
    # mdudir = os.path.dirname(arguments.mdu)
    # mduparser = MduParser(defaults=DEFAULTS)
    # mduparser.readfp(open(arguments.mdu))


    commentedmdu = MduParserKeepComments()
    commentedmdu.readfp(open(arguments.mdu))

    commentedmdu.set("model", "FileFormatVersion", "2.1")

    # http://docs.python.org/2/library/collections.html#ordereddict-objects    
    
    changes = collections.OrderedDict([
        (("geometry", "ManholeFile"), ("external forcing", "ManholeFile")),
        (("geometry", "FloodIniFile"), ("initialization", "FloodIniFile")),
        (("initialization", "WaterLevelFile"), ("initialization", "WaterLevelIniFile")),
        (("initialization", "FloodWaterLevel"), ("defaults", "FloodWaterLevel")),
        (("initialization", "FloodLevelAbsolute"), ("defaults", "FloodLevelAbsolute")),
        (("initialization", "BathymetryIncrement"), ("defaults", "BathymetryIncrement")),
        (("initialization", "BathIncAbsolute"), ("defaults", "BathIncAbsolute")),
        (("initialization", "InfiltrationRateNew"), ("defaults", "InfiltrationRateNew")),
        (("initialization", "Rainfall"), ("defaults", "RainfallCloudAmount")),
        (("initialization", "RainfallCloudDiameter"), ("defaults", "RainfallCloudDiameter")),
        (("Ground Water", ""), ("hydrology", "")),
        (("hydrology", "GroundwaterLevelFile"), ("hydrology", "GroundWaterLevelIniFile")),
        (("hydrology", "permability_x"), ("hydrology", "HydraulicConductivity_X")),
        (("hydrology", "permability_y"), ("hydrology", "HydraulicConductivity_Y")),
        (("hydrology", "GroundwaterLevelFile"), ("hydrology", "GroundWaterLevelIniFile")),
        (("output", "LogOut"), ("display", "RedrawEvery")),
        (("output", "SaveHardCopy"), ("display", "SaveHardCopy")),
        (("output", "showGrid"), ("display", "showGrid")),
        (("output", "showLinks"), ("display", "showLinks")),
        (("output", "Show1DNetwork"), ("display", "Show1DNetwork")),
        (("output", "ShowStructures"), ("display", "ShowStructures")),
        (("output", "ShowNetworkCRS"), ("display", "ShowNetworkCRS")),
        (("output", "ShowNodNumbers"), ("display", "ShowNodNumbers")),
        (("output", "Show1DNodNum"), ("display", "Show1DNodNum")),
        (("colors", "showInterception"), ("display", "showInterception")),
        (("colors", "ShowUZslice"), ("display", "ShowUZslice")),
        (("colors", "sliceUZcolor"), ("display", "sliceUZcolor")),
        (("colors", "showChanSelect"), ("display", "showChanSelect")),
        (("colors", "showChanMinY"), ("display", "showChanMinY")),
        (("colors", "showChanMaxY"), ("display", "showChanMaxY"))
    ])
#
#
    # todo: for loop across dict/or list? To be processed in order!
    # foreach
    #    if key1 == "" and key2 == "":
    #       rename_section(commentedmdu, sec1, sec2)
    #    else
    #       opt_rename(commentedmdu, sec1, sec2, key1, key2)
            # TODO:  need to catch NoOptionError from config.get??

    
    with open(arguments.mdu , 'w') as mdufile:
        comment = "# mdu file changed by {} at {}".format(
            sys.argv[0],
            datetime.datetime.now()
        )
        mdufile.write(comment + "\n")
        commentedmdu.write(mdufile)
