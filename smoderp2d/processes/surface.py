import tensorflow as tf


def shallowSurfaceKinematic(a, b, h_sheet):

    return tf.math.pow(h_sheet, b) * a
