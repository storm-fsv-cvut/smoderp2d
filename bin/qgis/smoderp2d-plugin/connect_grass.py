import os
import sys
import subprocess


def find_grass_bin():
    """Find GRASS binary."""
    try:
        grass_bin_path = _grass_loc()
    except ImportError as e:
        raise ImportError('Unable to find GRASS installation. {}'.format(e))

    return grass_bin_path


def _grass_loc():
    """Find GRASS instalation.
    :todo: Avoid bat file calling.
    """
    if sys.platform == 'win32':
        qgis_prefix_path = os.environ['QGIS_PREFIX_PATH']
        bin_path = os.path.join(qgis_prefix_path, '..', '..',  'bin')
        grass_bin_path = None

        for grass_version in range(83, 89):
            gpath = os.path.join(bin_path, 'grass{}.bat'.format(grass_version))
            if os.path.exists(gpath):
                grass_bin_path = gpath
                break

        if grass_bin_path is None:
            raise ImportError("No GRASS executable found.")
    else:
        grass_bin_path = '/usr/bin/grass'

    startcmd = [grass_bin_path, '--config', 'path']

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
    if os.environ.get('GISBASE') is None: # workaround for https://github.com/storm-fsv-cvut/smoderp2d/issues/278
        os.environ['GISBASE'] = gisbase
    # define GRASS-Python environment
    sys.path.append(os.path.join(gisbase, "etc", "python"))

    return grass_bin_path
