# Licensed under a 3-clause BSD style license - see LICENSE.rst

"""
The following are private functions, included here **FOR REFERENCE ONLY** since
the io registry cannot be displayed. These functions are registered into
:meth:`~astropy.cosmology.Cosmology.to_format` and
:meth:`~astropy.cosmology.Cosmology.from_format` and should only be accessed
via these methods.
"""  # this is shown in the docs.

import astropy.cosmology.units as cu
import astropy.units as u
from astropy.cosmology.core import _COSMOLOGY_CLASSES, Cosmology
from astropy.cosmology.connect import convert_registry
from astropy.io.misc.yaml import AstropyDumper, AstropyLoader, dump, load

from .mapping import from_mapping

__all__ = []  # nothing is publicly scoped


##############################################################################
# Serializer Functions
# these do Cosmology <-> YAML through a modified dictionary representation of
# the Cosmology object. The Unified-I/O functions are just wrappers to the YAML
# that calls these functions.


def yaml_representer(tag):
    """:mod:`yaml` representation of |Cosmology| object.

    Parameters
    ----------
    tag : str
        The class tag, e.g. '!astropy.cosmology.LambdaCDM'

    Returns
    -------
    representer : callable[[`~astropy.io.misc.yaml.AstropyDumper`, |Cosmology|], str]
        Function to construct :mod:`yaml` representation of |Cosmology| object.
    """
    def representer(dumper, obj):
        """Cosmology yaml representer function.

        Parameters
        ----------
        dumper : `~astropy.io.misc.yaml.AstropyDumper`
        obj : `~astropy.cosmology.Cosmology`

        Returns
        -------
        str
            :mod:`yaml` representation of |Cosmology| object.
        """
        # convert to mapping
        map = obj.to_format("mapping")
        # remove the cosmology class info. It's already recorded in `tag`
        map.pop("cosmology")
        # make the metadata serializable in an order-preserving way.
        map["meta"] = tuple(map["meta"].items())

        return dumper.represent_mapping(tag, map)

    return representer


def yaml_constructor(cls):
    """Cosmology| object from :mod:`yaml` representation.

    Parameters
    ----------
    cls : type
        The class type, e.g. `~astropy.cosmology.LambdaCDM`.

    Returns
    -------
    constructor : callable
        Function to construct |Cosmology| object from :mod:`yaml` representation.
    """
    def constructor(loader, node):
        """Cosmology yaml constructor function.

        Parameters
        ----------
        loader : `~astropy.io.misc.yaml.AstropyLoader`
        node : `yaml.nodes.MappingNode`
            yaml representation of |Cosmology| object.

        Returns
        -------
        `~astropy.cosmology.Cosmology` subclass instance
        """
        # create mapping from YAML node
        map = loader.construct_mapping(node)
        # restore metadata to dict
        map["meta"] = dict(map["meta"])
        # get cosmology class qualified name from node
        cosmology = str(node.tag).split(".")[-1]
        # create Cosmology from mapping
        return from_mapping(map, move_to_meta=False, cosmology=cosmology)

    return constructor


def register_cosmology_yaml(cosmo_cls):
    """Register :mod:`yaml` for Cosmology class.

    Parameters
    ----------
    cosmo_cls : `~astropy.cosmology.Cosmology` class
    """
    tag = f"!{cosmo_cls.__module__}.{cosmo_cls.__qualname__}"

    AstropyDumper.add_representer(cosmo_cls, yaml_representer(tag))
    AstropyLoader.add_constructor(tag, yaml_constructor(cosmo_cls))


##############################################################################
# Unified-I/O Functions


def from_yaml(yml):
    """Load `~astropy.cosmology.Cosmology` from :mod:`yaml` object.

    Parameters
    ----------
    yml : str
        :mod:`yaml` representation of |Cosmology| object

    Returns
    -------
    `~astropy.cosmology.Cosmology` subclass instance
    """
    with u.add_enabled_units(cu):
        return load(yml)


def to_yaml(cosmology, *args):
    """Return the cosmology class, parameters, and metadata as a :mod:`yaml` object.

    Parameters
    ----------
    cosmology : `~astropy.cosmology.Cosmology` subclass instance
    *args
        Not used. Needed for compatibility with
        `~astropy.io.registry.UnifiedReadWriteMethod`

    Returns
    -------
    str
        :mod:`yaml` representation of |Cosmology| object
    """
    return dump(cosmology)


# ``read`` cannot handle non-path strings.
#  TODO! this says there should be different types of I/O registries.
#        not just hacking object conversion on top of file I/O.
# def yaml_identify(origin, format, *args, **kwargs):
#     """Identify if object uses the yaml format.
#
#     Returns
#     -------
#     bool
#     """
#     itis = False
#     if origin == "read":
#         itis = isinstance(args[1], str) and args[1][0].startswith("!")
#         itis &= format in (None, "yaml")
#
#     return itis


# ===================================================================
# Register

for cosmo_cls in _COSMOLOGY_CLASSES.values():
    register_cosmology_yaml(cosmo_cls)

convert_registry.register_reader("yaml", Cosmology, from_yaml)
convert_registry.register_writer("yaml", Cosmology, to_yaml)
# convert_registry.register_identifier("yaml", Cosmology, yaml_identify)
