# coding: utf-8
#/*##########################################################################
# Copyright (C) 2016 European Synchrotron Radiation Facility
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
#############################################################################*/
"""Tests for specfile wrapper"""

__authors__ = ["P. Knobel"]
__license__ = "MIT"
__date__ = "29/04/2016"

import gc
import locale
import logging
import numpy
import os
import sys
import tempfile
import unittest

logging.basicConfig()
logger1 = logging.getLogger(__name__)

from ..specfile import SpecFile, Scan

sftext = """#F /tmp/sf.dat
#E 1455180875
#D Thu Feb 11 09:54:35 2016
#C imaging  User = opid17
#U00 user comment first line
#U01 This is a dummy file to test SpecFile parsing
#U02
#U03 last line

#O0 Pslit HGap  MRTSlit UP  MRTSlit DOWN
#O1 Sslit1 VOff  Sslit1 HOff  Sslit1 VGap
#o0 pshg mrtu mrtd
#o2 ss1vo ss1ho ss1vg

#J0 Seconds  IA  ion.mono  Current
#J1 xbpmc2  idgap1  Inorm

#S 1  ascan  ss1vo -4.55687 -0.556875  40 0.2
#D Thu Feb 11 09:55:20 2016
#T 0.2  (Seconds)
#G0 0
#G1 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0
#G3 0 0 0 0 0 0 0 0 0
#G4 0
#Q
#P0 180.005 -0.66875 0.87125
#P1 14.74255 16.197579 12.238283
#UMI0     Current AutoM      Shutter
#UMI1      192.51   OFF     FE open
#UMI2 Refill in 39883 sec, Fill Mode: uniform multibunch / Message: Feb 11 08:00 Delivery:Next Refill at 21:00;
#N 4
#L first column  second column  3rd_col
-1.23 5.89  8
8.478100E+01  5 1.56
3.14 2.73 -3.14
1.2 2.3 3.4

#S 25  ascan  c3th 1.33245 1.52245  40 0.15
#D Thu Feb 11 10:00:31 2016
#P0 80.005 -1.66875 1.87125
#P1 4.74255 6.197579 2.238283
#N 5
#L column0  column1  col2  col3
0.0 0.1 0.2 0.3
1.0 1.1 1.2 1.3
2.0 2.1 2.2 2.3
3.0 3.1 3.2 3.3

#F /tmp/sf.dat
#E 1455180876
#D Thu Feb 11 09:54:36 2016

#S 1 aaaaaa
#U first duplicate line
#U second duplicate line
#@MCADEV 1
#@MCA %16C
#@CHANN 3 0 2 1
#@CALIB 1 2 3
#N 3
#L uno  duo
1 2
@A 0 1 2
3 4
@A 3.1 4 5
5 6
@A 6 7.7 8
"""

loc = locale.getlocale(locale.LC_NUMERIC)
try:
    locale.setlocale(locale.LC_NUMERIC, 'de_DE.utf8')
except locale.Error:
    try_DE = False
else:
    try_DE = True
    locale.setlocale(locale.LC_NUMERIC, loc)


class TestSpecFile(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        fd, cls.fname1 = tempfile.mkstemp(text=False)
        if sys.version < '3.0':
            os.write(fd, sftext)
        else:
            os.write(fd, bytes(sftext, 'ascii'))
        os.close(fd)

        fd2, cls.fname2 = tempfile.mkstemp(text=False)
        if sys.version < '3.0':
            os.write(fd2, sftext[370:-97])
        else:
            os.write(fd2, bytes(sftext[370:-97], 'ascii'))
        os.close(fd2)

    @classmethod
    def tearDownClass(cls):
        os.unlink(cls.fname1)
        os.unlink(cls.fname2)


    def setUp(self):
        self.sf = SpecFile(self.fname1)
        self.scan1 = self.sf[0]
        self.scan1_2 = self.sf["1.2"]
        self.scan25 = self.sf["25.1"]

        self.sf_no_fhdr = SpecFile(self.fname2)
        self.scan1_no_fhdr = self.sf_no_fhdr[0]

    def tearDown(self):
        del self.sf
        del self.sf_no_fhdr
        del self.scan1
        del self.scan1_2
        del self.scan25
        del self.scan1_no_fhdr
        gc.collect()

    def test_open(self):
        self.assertIsInstance(self.sf, SpecFile)
        with self.assertRaises(IOError):
            sf2 = SpecFile("doesnt_exist.dat")
        
    def test_number_of_scans(self):
        self.assertEqual(3, len(self.sf))
        
    def test_list_of_scan_indices(self):
        self.assertEqual(self.sf.list(),
                         [1, 25, 1])
        self.assertEqual(self.sf.keys(),
                         ["1.1", "25.1", "1.2"])

    def test_index_number_order(self):
        self.assertEqual(self.sf.index(1, 2), 2)  #sf["1.2"]==sf[2]
        self.assertEqual(self.sf.number(1), 25)   #sf[1]==sf["25"]
        self.assertEqual(self.sf.order(2), 2)     #sf[2]==sf["1.2"]
        with self.assertRaises(IndexError):
            self.sf.index(3, 2)
        with self.assertRaises(IndexError):
            self.sf.index(99)
        
    def test_getitem(self):
        self.assertIsInstance(self.sf[2], Scan)
        self.assertIsInstance(self.sf["1.2"], Scan)
        # int out of range
        with self.assertRaisesRegexp(IndexError, 'Scan index must be in ran'):
            self.sf[107]
        # float indexing not allowed
        with self.assertRaisesRegexp(TypeError, 'The scan identification k'):
            self.sf[1.2]
        # non existant scan with "N.M" indexing 
        with self.assertRaises(KeyError):
            self.sf["3.2"]

    def test_specfile_iterator(self):
        i=0
        for scan in self.sf:
            if i == 1:
                self.assertEqual(scan.motor_positions,
                                 self.sf[1].motor_positions)
            i += 1
        # number of returned scans
        self.assertEqual(i, len(self.sf))

    def test_scan_index(self):
        self.assertEqual(self.scan1.index, 0)
        self.assertEqual(self.scan1_2.index, 2)
        self.assertEqual(self.scan25.index, 1)

    def test_scan_headers(self):
        self.assertEqual(self.scan25.scan_header_dict['S'],
                         "25  ascan  c3th 1.33245 1.52245  40 0.15")
        self.assertEqual(self.scan1.header[17], '#G0 0')
        self.assertEqual(len(self.scan1.header), 29)
        # parsing headers with long keys
        self.assertEqual(self.scan1.scan_header_dict['UMI0'],
                         'Current AutoM      Shutter')
        # parsing empty headers
        self.assertEqual(self.scan1.scan_header_dict['Q'], '')
        # duplicate headers: concatenated (with newline)
        self.assertEqual(self.scan1_2.scan_header_dict["U"],
                         "first duplicate line\nsecond duplicate line")

    def test_file_headers(self):
        self.assertEqual(self.scan1.header[1],
                         '#E 1455180875')
        self.assertEqual(self.scan1.file_header_dict['F'],
                         '/tmp/sf.dat')

    def test_multiple_file_headers(self):
        """Scan 1.2 is after the second file header, with a different
        Epoch"""
        self.assertEqual(self.scan1_2.header[1],
                         '#E 1455180876')
        
    def test_scan_labels(self):
        self.assertEqual(self.scan1.labels,
                         ['first column', 'second column', '3rd_col'])

    def test_data(self):
        self.assertAlmostEqual(self.scan1.data_line(1)[2],
                               1.56)
        self.assertEqual(self.scan1.data.shape, (4, 3))
        self.assertAlmostEqual(numpy.sum(self.scan1.data), 113.631)

    def test_data_column_by_name(self):
        self.assertAlmostEqual(self.scan25.data_column_by_name("col2")[1],
                               1.2)
        self.assertAlmostEqual(numpy.sum(self.scan25.data_column_by_name("col2")),
                               numpy.sum(self.scan25.data[:, 2]))
        with self.assertRaises(KeyError):
            self.scan25.data_column_by_name("ygfxgfyxg")

    def test_motors(self):
        self.assertEqual(len(self.scan1.motor_names), 6)
        self.assertEqual(len(self.scan1.motor_positions), 6)
        self.assertAlmostEqual(sum(self.scan1.motor_positions),
                               223.385912)
        self.assertEqual(self.scan1.motor_names[1], 'MRTSlit UP')
        self.assertAlmostEqual(
            self.scan25.motor_position_by_name('MRTSlit UP'),
            -1.66875)

    def test_absence_of_file_header(self):
        """We expect Scan.file_header to be an empty list in the absence
        of a file header.

        Important note: A #S line needs to be preceded  by an empty line,
        so a SpecFile without a file header needs to start with an empty line.
        Otherwise, this test fails because SfFileHeader() fills
        Scan.file_header with 15 scan header lines.
        """
        self.assertEqual(len(self.scan1_no_fhdr.motor_names), 0)
        # motor positions can still be read in the scan header
        # even in the absence of motor names
        self.assertAlmostEqual(sum(self.scan1_no_fhdr.motor_positions),
                               223.385912)
        self.assertEqual(len(self.scan1_no_fhdr.header), 15)
        self.assertEqual(len(self.scan1_no_fhdr.file_header), 0)

    def test_mca(self):
        self.assertEqual(len(self.scan1.mca), 0)
        self.assertEqual(len(self.scan1_2.mca), 3)
        self.assertEqual(self.scan1_2.mca[1][2], 5)
        self.assertEqual(sum(self.scan1_2.mca[2]), 21.7)

        # Negative indexing
        self.assertEqual(sum(self.scan1_2.mca[len(self.scan1_2.mca)-1]),
                         sum(self.scan1_2.mca[-1]))

        # Test iterator
        line_count, total_sum = (0, 0)
        for mca_line in self.scan1_2.mca:
            line_count += 1
            total_sum += sum(mca_line)
        self.assertEqual(line_count, 3)
        self.assertAlmostEqual(total_sum, 36.8)

    def test_mca_header(self):
        self.assertEqual(self.scan1.mca_header_dict, {})
        self.assertEqual(len(self.scan1_2.mca_header_dict), 4)
        self.assertEqual(self.scan1_2.mca_header_dict["CALIB"], "1 2 3")
        self.assertEqual(self.scan1_2.mca.calibration,
                         [1., 2., 3.])
        # default calib in the absence of #@CALIB
        self.assertEqual(self.scan25.mca.calibration,
                         [0., 1., 0.])
        self.assertEqual(self.scan1_2.mca.channels,
                         [0, 1, 2])
        # absence of #@CHANN and spectra
        self.assertIs(self.scan25.mca.channels,
                      None)


class TestSFLocale(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        fd, cls.fname = tempfile.mkstemp(text=False)
        if sys.version < '3.0':
            os.write(fd, sftext)
        else:
            os.write(fd, bytes(sftext, 'ascii'))
        os.close(fd)

    @classmethod
    def tearDownClass(cls):
        os.unlink(cls.fname)
        locale.setlocale(locale.LC_NUMERIC, loc)  # restore saved locale
        gc.collect()

    def crunch_data(self):
        self.sf3 = SpecFile(self.fname)
        self.assertAlmostEqual(self.sf3[0].data_line(1)[2],
                               1.56)
        del self.sf3

    @unittest.skipIf(not try_DE, "de_DE.utf8 locale not installed")
    def test_locale_de_DE(self):
        locale.setlocale(locale.LC_NUMERIC, 'de_DE.utf8')
        self.crunch_data()

    def test_locale_user(self):
        locale.setlocale(locale.LC_NUMERIC, '')  # use user's preferred locale
        self.crunch_data()

    def test_locale_C(self):
        locale.setlocale(locale.LC_NUMERIC, 'C')  # use default (C) locale
        self.crunch_data()


def suite():
    test_suite = unittest.TestSuite()
    test_suite.addTest(
        unittest.defaultTestLoader.loadTestsFromTestCase(TestSpecFile))
    test_suite.addTest(
        unittest.defaultTestLoader.loadTestsFromTestCase(TestSFLocale))
    return test_suite


if __name__ == '__main__':
    unittest.main(defaultTest="suite")