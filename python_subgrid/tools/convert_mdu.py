"""Convert scriptlets

* convert_subgrid_mdu: translate an old formatted MDU file (version < 2) to
  the new v2.1 structure.

"""

import argparse
import sys
import datetime
import collections
import ConfigParser
import logging
import re

from python_subgrid.utils import MduParserKeepComments

# TODO: move logging setup to the main()
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


def parse_args():
    """
    Parse the command line arguments
    """
    argumentparser = argparse.ArgumentParser(
        description='Convert an old MDU (version < 2) to the new structure.')
    argumentparser.add_argument(
        'mdu',
        help='mdu files to process, will be overwritten!')
    arguments = argumentparser.parse_args()

    return arguments


########################
# TODO: move to utils?
def rename_section(config, section1, section2):
    """rename section1 to section2 in the config object"""

    logger.debug("Rename: [{}] -> [{}].".format(section1, section2))
    # lookup all items in section1
    try:
        items = config.items(section1)
    except ConfigParser.NoSectionError:
        # If section1 does not exist, let it pass.
        logger.info("rename_section: Section %s does not exist. Passing.",
                    section1)
        return

    # add section 2
    config.add_section(section2)
    # copy all items from section1 to section2
    for option, value in items:
        config.set(section2, option, value)

    config.remove_section(section1)


# TODO: move to utils?
def opt_rename(config, section1, section2, option1, option2):
    """rename section1, option1  to section2, option2 """
    if section1 == section2:
        logger.debug("Rename under [%s]: %s -> %s.",
                     section1, option1, option2)
    elif option1 == option2:
        logger.debug("Move %s: from [%s] -> [%s].",
                     option1, section1, section2)
    else:
        logger.debug("Converting: [%s] %s -> [%s] %s.",
                     section1, option1, section2, option2)
    try:
        config.set(section2, option2, config.get(section1, option1, 1))
    except ConfigParser.NoSectionError:
        # Create non-existent section
        logger.debug("opt_rename: Adding section '%s'.", section2)
        config.add_section(section2)
        opt_rename(config, section1, section2, option1, option2)
    except ConfigParser.NoOptionError:
        # If section1, option1 does not exist, let it pass.
        logger.info("opt_rename: Original option '%s' not present " +
                    "under [%s]. Passing.",
                    option1, section1)
        pass
    else:
        config.remove_option(section1, option1)


# Allow to use mdu file from any directory
# Script will be run like this:
# find . -name *.mdu -exec update-subgrid-mdu {} \;
def main():
    """Change mdu file to new version >=2.0 MDU File Format"""
    arguments = parse_args()

    # Read mdu file

    commentedmdu = MduParserKeepComments()
    commentedmdu.readfp(open(arguments.mdu))

    # Check current version:
    try:
        inputversion = commentedmdu.get("model", "FileFormatVersion")
    except ConfigParser.NoOptionError:
        inputversion = "0.0"

    match = re.match(r"""\d+""", inputversion)
    if match is not None:
        inputmajorv = int(match.group())
    else:
        inputmajorv = 0

    outputversion = "2.2"
    outputmajorv = int(float(outputversion))

    if inputmajorv >= outputmajorv:
        logger.info("Input file %s is already recent enough: " +
                    "major version %s >= %s. Exiting.",
                    arguments.mdu, inputmajorv, outputmajorv)
        return

    # Input file is indeed old, now proceed with the actual conversion.
    logger.info("Converting {} -> {}...".format(inputversion, outputversion))

    commentedmdu.set("model", "FileFormatVersion", outputversion)

    # Define the renamings
    changes = collections.OrderedDict([
        (("geometry", "ManholeFile"),
         ("external forcing", "ManholeFile")),
        (("geometry", "FloodIniFile"),
         ("initialization", "FloodIniFile")),
        (("initialization", "WaterLevelFile"),
         ("initialization", "WaterLevelIniFile")),
        (("initialization", "FloodWaterLevel"),
         ("defaults", "FloodWaterLevel")),
        (("initialization", "FloodLevelAbsolute"),
         ("defaults", "FloodLevelAbsolute")),
        (("initialization", "BathymetryIncrement"),
         ("defaults", "BathymetryIncrement")),
        (("initialization", "BathIncAbsolute"),
         ("defaults", "BathIncAbsolute")),
        (("initialization", "InfiltrationRateNew"),
         ("defaults", "InfiltrationRateNew")),
        (("initialization", "Rainfall"),
         ("defaults", "RainfallCloudAmount")),
        (("initialization", "RainfallCloudDiameter"),
         ("defaults", "RainfallCloudDiameter")),
        (("Ground Water", ""),
         ("hydrology", "")),
        (("hydrology", "GroundwaterLevelFile"),
         ("hydrology", "GroundWaterLevelIniFile")),
        (("hydrology", "permeability_x"),
         ("hydrology", "HydraulicConductivity_X")),
        (("hydrology", "permeability_y"),
         ("hydrology", "HydraulicConductivity_Y")),
        (("hydrology", "GroundwaterLevelFile"),
         ("hydrology", "GroundWaterLevelIniFile")),
        (("output", "LogOut"),
         ("display", "RedrawEvery")),
        (("output", "SaveHardCopy"),
         ("display", "SaveHardCopy")),
        (("output", "showGrid"),
         ("display", "showGrid")),
        (("output", "showLinks"),
         ("display", "showLinks")),
        (("output", "Show1DNetwork"),
         ("display", "Show1DNetwork")),
        (("output", "ShowStructures"),
         ("display", "ShowStructures")),
        (("output", "ShowNetworkCRS"),
         ("display", "ShowNetworkCRS")),
        (("output", "ShowNodNumbers"),
         ("display", "ShowNodNumbers")),
        (("output", "Show1DNodNum"),
         ("display", "Show1DNodNum")),
        (("colors", "showInterception"),
         ("display", "showInterception")),
        (("colors", "ShowUZslice"),
         ("display", "ShowUZslice")),
        (("colors", "sliceUZcolor"),
         ("display", "sliceUZcolor")),
        (("colors", "showChanSelect"),
         ("display", "showChanSelect")),
        (("colors", "showChanMinY"),
         ("display", "showChanMinY")),
        (("colors", "showChanMaxY"),
         ("display", "showChanMaxY"))
    ])

    # Perform the renamings
    for (sec1, opt1), (sec2, opt2) in changes.items():
        if opt1 == "" and opt2 == "":
            rename_section(commentedmdu, sec1, sec2)
        else:
            opt_rename(commentedmdu, sec1, sec2, opt1, opt2)

    # Write the new MDU file
    with open(arguments.mdu, 'w') as mdufile:
        comment = "# mdu file changed by {} at {}".format(
            sys.argv[0],
            datetime.datetime.now()
        )
        mdufile.write(comment + "\n")
        commentedmdu.write(mdufile)
