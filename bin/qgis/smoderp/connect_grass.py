import os
import sys
import subprocess
import shutil
import tempfile


def findGrass():
    try:
        grass7bin = _grassLoc()
    except ImportError as e:
        raise ImportError('Unable to find GRASS installation. {}'.format(e))
    return grass7bin


def _grassLoc():
    """Find GRASS.
    Find location of GRASS.
    :todo: Avoid bat file calling.
    """
    ########### SOFTWARE
    if sys.platform == 'win32':
        qgis_prefix_path = os.environ['QGIS_PREFIX_PATH']
        bin_path = os.path.join(os.path.split(
            os.path.split(qgis_prefix_path)[0])[0],
            'bin'
        )
        grass7bin = None
        for grass_version in ['70', '72', '74']:
            gpath = os.path.join(bin_path, 'grass{}.bat'.format(grass_version))
            if os.path.exists(gpath):
                grass7bin = gpath
                break

        if grass7bin is None:
            raise ImportError("No grass70.bat or grass72.bat or grass74.bat found.")
    else:
        grass7bin = '/usr/bin/grass'
    startcmd = [grass7bin, '--config', 'path']

    p = subprocess.Popen(startcmd,
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = p.communicate()

    if p.returncode != 0:
        raise ImportError("Reason: ({cmd}: {reason})".format(
            cmd=startcmd, reason=err)
        )

    str_out = out.decode("utf-8")
    gisbase = str_out.rstrip(os.linesep)

    # Set GISBASE environment variable
    os.environ['GISBASE'] = gisbase
    # define GRASS-Python environment
    sys.path.append(os.path.join(gisbase, "etc", "python"))

    return grass7bin
