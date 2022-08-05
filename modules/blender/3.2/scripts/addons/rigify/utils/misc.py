# SPDX-License-Identifier: GPL-2.0-or-later

import bpy
import math
import collections

from itertools import tee, chain, islice, repeat, permutations
from mathutils import Vector, Matrix, Color
from rna_prop_ui import rna_idprop_value_to_python


#=============================================
# Math
#=============================================


axis_vectors = {
    'x': (1,0,0),
    'y': (0,1,0),
    'z': (0,0,1),
    '-x': (-1,0,0),
    '-y': (0,-1,0),
    '-z': (0,0,-1),
}


# Matrices that reshuffle axis order and/or invert them
shuffle_matrix = {
    sx+x+sy+y+sz+z: Matrix((
        axis_vectors[sx+x], axis_vectors[sy+y], axis_vectors[sz+z]
        )).transposed().freeze()
    for x, y, z in permutations(['x', 'y', 'z'])
    for sx in ('', '-')
    for sy in ('', '-')
    for sz in ('', '-')
}


def angle_on_plane(plane, vec1, vec2):
    """ Return the angle between two vectors projected onto a plane.
    """
    plane.normalize()
    vec1 = vec1 - (plane * (vec1.dot(plane)))
    vec2 = vec2 - (plane * (vec2.dot(plane)))
    vec1.normalize()
    vec2.normalize()

    # Determine the angle
    angle = math.acos(max(-1.0, min(1.0, vec1.dot(vec2))))

    if angle < 0.00001:  # close enough to zero that sign doesn't matter
        return angle

    # Determine the sign of the angle
    vec3 = vec2.cross(vec1)
    vec3.normalize()
    sign = vec3.dot(plane)
    if sign >= 0:
        sign = 1
    else:
        sign = -1

    return angle * sign


# Convert between a matrix and axis+roll representations.
# Re-export the C implementation internally used by bones.
matrix_from_axis_roll = bpy.types.Bone.MatrixFromAxisRoll
axis_roll_from_matrix = bpy.types.Bone.AxisRollFromMatrix


def matrix_from_axis_pair(y_axis, other_axis, axis_name):
    assert axis_name in 'xz'

    y_axis = Vector(y_axis).normalized()

    if axis_name == 'x':
        z_axis = Vector(other_axis).cross(y_axis).normalized()
        x_axis = y_axis.cross(z_axis)
    else:
        x_axis = y_axis.cross(other_axis).normalized()
        z_axis = x_axis.cross(y_axis)

    return Matrix((x_axis, y_axis, z_axis)).transposed()


#=============================================
# Color correction functions
#=============================================


def linsrgb_to_srgb (linsrgb):
    """Convert physically linear RGB values into sRGB ones. The transform is
    uniform in the components, so *linsrgb* can be of any shape.

    *linsrgb* values should range between 0 and 1, inclusively.

    """
    # From Wikipedia, but easy analogue to the above.
    gamma = 1.055 * linsrgb**(1./2.4) - 0.055
    scale = linsrgb * 12.92
    # return np.where (linsrgb > 0.0031308, gamma, scale)
    if linsrgb > 0.0031308:
        return gamma
    return scale


def gamma_correct(color):

    corrected_color = Color()
    for i, component in enumerate(color):
        corrected_color[i] = linsrgb_to_srgb(color[i])
    return corrected_color


#=============================================
# Iterators
#=============================================


def padnone(iterable, pad=None):
    return chain(iterable, repeat(pad))


def pairwise_nozip(iterable):
    "s -> (s0,s1), (s1,s2), (s2,s3), ..."
    a, b = tee(iterable)
    next(b, None)
    return a, b


def pairwise(iterable):
    "s -> (s0,s1), (s1,s2), (s2,s3), ..."
    a, b = tee(iterable)
    next(b, None)
    return zip(a, b)


def map_list(func, *inputs):
    "[func(a0,b0...), func(a1,b1...), ...]"
    return list(map(func, *inputs))


def skip(n, iterable):
    "Returns an iterator skipping first n elements of an iterable."
    iterator = iter(iterable)
    if n == 1:
        next(iterator, None)
    else:
        next(islice(iterator, n, n), None)
    return iterator


def map_apply(func, *inputs):
    "Apply the function to inputs like map for side effects, discarding results."
    collections.deque(map(func, *inputs), maxlen=0)


#=============================================
# Lazy references
#=============================================


def force_lazy(value):
    """If the argument is callable, invokes it without arguments. Otherwise returns the argument as is."""
    if callable(value):
        return value()
    else:
        return value


class LazyRef:
    """Hashable lazy reference. When called, evaluates (foo, 'a', 'b'...) as foo('a','b')
    if foo is callable. Otherwise the remaining arguments are used as attribute names or
    keys, like foo.a.b or foo.a[b] etc."""

    def __init__(self, first, *args):
        self.first = first
        self.args = tuple(args)
        self.first_hashable = first.__hash__ is not None

    def __repr__(self):
        return 'LazyRef{}'.format(tuple(self.first, *self.args))

    def __eq__(self, other):
        return (
            isinstance(other, LazyRef) and
            (self.first == other.first if self.first_hashable else self.first is other.first) and
            self.args == other.args
        )

    def __hash__(self):
        return (hash(self.first) if self.first_hashable else hash(id(self.first))) ^ hash(self.args)

    def __call__(self):
        first = self.first
        if callable(first):
            return first(*self.args)

        for item in self.args:
            if isinstance(first, (dict, list)):
                first = first[item]
            else:
                first = getattr(first, item)

        return first


#=============================================
# Misc
#=============================================


def copy_attributes(a, b):
    keys = dir(a)
    for key in keys:
        if not key.startswith("_") \
        and not key.startswith("error_") \
        and key != "group" \
        and key != "is_valid" \
        and key != "rna_type" \
        and key != "bl_rna":
            try:
                setattr(b, key, getattr(a, key))
            except AttributeError:
                pass


def property_to_python(value):
    value = rna_idprop_value_to_python(value)

    if isinstance(value, dict):
        return { k: property_to_python(v) for k, v in value.items() }
    elif isinstance(value, list):
        return map_list(property_to_python, value)
    else:
        return value


def clone_parameters(target):
    return property_to_python(dict(target))


def assign_parameters(target, val_dict=None, **params):
    if val_dict is not None:
        for key in list(target.keys()):
            del target[key]

        data = { **val_dict, **params }
    else:
        data = params

    for key, value in data.items():
        try:
            target[key] = value
        except Exception as e:
            raise Exception("Couldn't set {} to {}: {}".format(key,value,e))


def select_object(context, object, deselect_all=False):
    view_layer = context.view_layer

    if deselect_all:
        for objt in view_layer.objects:
            objt.select_set(False)  # deselect all objects

    object.select_set(True)
    view_layer.objects.active = object
