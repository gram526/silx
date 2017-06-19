# coding: utf-8
# /*##########################################################################
#
# Copyright (c) 2016-2017 European Synchrotron Radiation Facility
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
"""Bunch of useful decorators"""

from __future__ import absolute_import, print_function, division

__authors__ = ["Jerome Kieffer"]
__license__ = "MIT"
__date__ = "16/06/2017"

import sys
import logging
import functools
import os
import traceback

depreclog = logging.getLogger("silx.DEPRECATION")


def deprecated(func=None, reason=None, replacement=None, since_version=None):
    """
    Decorator that deprecates the use of a function

    :param str reason: Reason for deprecating this function
        (e.g. "feature no longer provided",
    :param str replacement: Name of replacement function (if the reason for
        deprecating was to rename the function)
    :param str since_version: First *silx* version for which the function was
        deprecated (e.g. "0.5.0").
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            name = func.func_name if sys.version_info[0] < 3 else func.__name__

            deprecated_warning(type='function',
                               name=name,
                               reason=reason,
                               replacement=replacement,
                               since_version=since_version)
            return func(*args, **kwargs)
        return wrapper
    if func is not None:
        return decorator(func)
    return decorator


def deprecated_warning(type_, name, reason=None, replacement=None,
                       since_version=None):
    """
    Decorator that deprecates the use of a function

    :param str type_: Module, function, class ...
    :param str reason: Reason for deprecating this function
        (e.g. "feature no longer provided",
    :param str replacement: Name of replacement function (if the reason for
        deprecating was to rename the function)
    :param str since_version: First *silx* version for which the function was
        deprecated (e.g. "0.5.0").
    """
    msg = "%s, %s is deprecated"
    if since_version is not None:
        msg += " since silx version %s" % since_version
    msg += "!"
    if reason is not None:
        msg += " Reason: %s." % reason
    if replacement is not None:
        msg += " Use '%s' instead." % replacement
    depreclog.warning(msg + " %s", type_, name,
                      os.linesep.join([""] + traceback.format_stack()[:-1]))