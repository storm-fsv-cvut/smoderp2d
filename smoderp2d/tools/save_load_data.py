"""Save and load data to with a pickle package.
"""

import os
import pickle
import sys

from smoderp2d.providers import Logger

def save_data(data, filename):
    """Save data into pickle.
    """
    dirname = os.path.dirname(filename)
    if not os.path.exists(dirname):
        os.makedirs(dirname)

    with open(filename, 'wb') as fd:
        pickle.dump(data, fd)
    Logger.debug('Size of saved data is {} bytes'.format(
        sys.getsizeof(data))
    )

def load_data(filename):
    """Load data from pickle.

    :param str filename: file to be loaded
    """
    with open(filename, 'rb') as fd:
        if sys.version_info > (3, 0):
            data = pickle.load(fd, encoding='bytes')
            data = {
                key.decode(): val.decode if isinstance(val, bytes) else val for key, val in data.items()
            }
        else:
            data = pickle.load(fd)
    Logger.debug('Size of loaded data is {} bytes'.format(
        sys.getsizeof(data))
    )

    return data
