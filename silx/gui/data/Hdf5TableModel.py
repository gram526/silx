# coding: utf-8
# /*##########################################################################
#
# Copyright (c) 2017 European Synchrotron Radiation Facility
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#
# ###########################################################################*/
"""
This module  define model and widget to display 1D slices from numpy
array using compound data types or hdf5 databases.
"""
from __future__ import division

__authors__ = ["V. Valls"]
__license__ = "MIT"
__date__ = "20/01/2017"

from silx.gui import qt
import os.path
import silx.io
from .TextFormatter import TextFormatter
import silx.gui.hdf5
import logging

_logger = logging.getLogger(__name__)


class _Property(object):
    """Store a label and a getter

    :param str label: Label of this property
    :param callable getter: Callable taking an object as unique argument and
        returning a string value.
    """

    def __init__(self, label, getter):
        self.__label = label
        self.__getter = getter

    def label(self):
        """Returns the label of the property.

        :rtype: str
        """
        return self.__label

    def value(self, obj):
        """Returns the value from the getter.

        :param object obj: Object in which the object is applied
        :rtype: str
        """
        return self.__getter(obj)


class Hdf5TableModel(qt.QAbstractTableModel):
    """This data model provides access to HDF5 node content (File, Group,
    Dataset). Main info, like name, file, attributes... are displayed

    :param qt.QObject parent: Parent object
    :param object data: An h5py-like object (file, group or dataset)
    """
    def __init__(self, parent=None, data=None):
        qt.QAbstractTableModel.__init__(self, parent)

        self.__obj = None
        self.__properties = []
        self.__formatter = TextFormatter()

        # set _data
        self.setObject(data)

    # Methods to be implemented to subclass QAbstractTableModel
    def rowCount(self, parent_idx=None):
        """Returns number of rows to be displayed in table"""
        return len(self.__properties)

    def columnCount(self, parent_idx=None):
        """Returns number of columns to be displayed in table"""
        return 1

    def data(self, index, role=qt.Qt.DisplayRole):
        """QAbstractTableModel method to access data values
        in the format ready to be displayed"""
        if not index.isValid():
            return None

        if self.__properties is None:
            return None

        if index.row() >= len(self.__properties):
            return None
        if index.column() >= 1:
            return None

        prop = self.__properties[index.row()]
        if role == qt.Qt.DisplayRole:
            if index.column() == 0:
                data = prop.value(self.__obj)
                return str(data)
        return None

    def headerData(self, section, orientation, role=qt.Qt.DisplayRole):
        """Returns the 0-based row or column index, for display in the
        horizontal and vertical headers"""
        if role == qt.Qt.DisplayRole:
            if orientation == qt.Qt.Vertical:
                if self.__properties is None:
                    return None
                if section >= len(self.__properties):
                    return None
                prop = self.__properties[section]
                return prop.label()
            if orientation == qt.Qt.Horizontal:
                if self.__properties is not None:
                    if section == 0:
                        return "HDF5 object"
                    else:
                        return None
        return None

    def flags(self, index):
        """QAbstractTableModel method to inform the view whether data
        is editable or not.
        """
        return qt.QAbstractTableModel.flags(self, index)

    def isSupportedObject(self, h5pyObject):
        """
        Returns true if the provided object can be modelized using this model.
        """
        isSupported = False
        isSupported = isSupported or silx.io.is_group(h5pyObject)
        isSupported = isSupported or silx.io.is_dataset(h5pyObject)
        isSupported = isSupported or isinstance(h5pyObject, silx.gui.hdf5.H5Node)
        return isSupported

    def setObject(self, h5pyObject):
        """Set the h5py-like object

        You can set ``copy=False`` if you need more performances, when dealing
        with a large numpy array. In this case, a simple reference to the data
        is used to access the data, rather than a copy of the array.

        .. warning::

            Any change to the data model will affect your original data
            array, when using a reference rather than a copy..

        :param data: 1D numpy array, or any object that can be
            converted to a numpy array using ``numpy.array(data)`` (e.g.
            a nested sequence).
        """
        if qt.qVersion() > "4.6":
            self.beginResetModel()

        if h5pyObject is None or self.isSupportedObject(h5pyObject):
            self.__obj = h5pyObject
        else:
            _logger.warning("Object class %s unsupported. Object ignored.", type(h5pyObject))
        self.__initProperties()

        if qt.qVersion() > "4.6":
            self.endResetModel()
        else:
            self.reset()

    def __initProperties(self):
        """Initialize the list of available properties according to the defined
        h5py-like object."""
        self.__properties = []
        if self.__obj is None:
            return

        obj = self.__obj

        if silx.io.is_file(obj):
            self.__properties.append(_Property("Type", lambda x: "File"))
        elif silx.io.is_group(obj):
            self.__properties.append(_Property("Type", lambda x: "Group"))
        elif silx.io.is_dataset(obj):
            self.__properties.append(_Property("Type", lambda x: "Dataset"))

        self.__properties.append(_Property("basename", lambda x: os.path.basename(x.name)))
        self.__properties.append(_Property("name", lambda x: x.name))
        if silx.io.is_file(obj):
            self.__properties.append(_Property("filename", lambda x: x.filename))

        if isinstance(obj, silx.gui.hdf5.H5Node):
            # helpful informations if the object come from an HDF5 tree
            self.__properties.append(_Property("local_basename", lambda x: x.local_basename))
            self.__properties.append(_Property("local_name", lambda x: x.local_name))
            self.__properties.append(_Property("local_filename", lambda x: x.local_file.filename))

        if hasattr(obj, "dtype"):
            self.__properties.append(_Property("dtype", lambda x: x.dtype))
        if hasattr(obj, "shape"):
            self.__properties.append(_Property("shape", lambda x: x.shape))
        if hasattr(obj, "size"):
            self.__properties.append(_Property("size", lambda x: x.size))
        if hasattr(obj, "compression"):
            self.__properties.append(_Property("compression", lambda x: x.compression))
        if hasattr(obj, "compression_opts"):
            self.__properties.append(_Property("compression_opts", lambda x: x.compression_opts))

        if hasattr(obj, "attrs"):
            for key in sorted(obj.attrs.keys()):
                name = "attrs[%s]" % key
                self.__properties.append(_Property(name, lambda x: self.__formatter.toString(x.attrs[key])))

    def object(self):
        """Returns the internal object modelized.

        :rtype: An h5py-like object
        """
        return self.__obj

    def setFloatFormat(self, numericFormat):
        """Set format string controlling how the values are represented in
        the table view.

        :param str numericFormat: Format string (e.g. "%.3f", "%d", "%-10.2f",
            "%10.3e").
            This is the C-style format string used by python when formatting
            strings with the modulus operator.
        """
        if qt.qVersion() > "4.6":
            self.beginResetModel()

        self.__formatter.setFloatFormat(numericFormat)

        if qt.qVersion() > "4.6":
            self.endResetModel()
        else:
            self.reset()
