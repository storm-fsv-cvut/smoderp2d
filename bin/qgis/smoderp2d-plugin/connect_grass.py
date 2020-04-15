import os
import sys
import subprocess
import shutil
import tempfile


def find_grass():
    try:
        grass7bin = _grass_loc()
    except ImportError as e:
        raise ImportError('Unable to find GRASS installation. {}'.format(e))
    return grass7bin


def _grass_loc():
    """Find GRASS instalation.
    :todo: Avoid bat file calling.
    """
    if sys.platform == 'win32':
        qgis_prefix_path = os.environ['QGIS_PREFIX_PATH']
        bin_path = os.path.join(qgis_prefix_path, '..', '..',  'bin')
        grass7bin = None
        for grass_version in ['77', '78']:
            gpath = os.path.join(bin_path, 'grass{}.bat'.format(grass_version))
            if os.path.exists(gpath):
                grass7bin = gpath
                break

        if grass7bin is None:
            raise ImportError("No grass executable found.")
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
