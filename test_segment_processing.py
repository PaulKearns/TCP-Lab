#
# Columbia University - CSEE 4119 Computer Networks
# Assignment 2 - Mini Reliable Transport Protocol
#
# test_segment_processing.py - testing file used as unit test for segment processing
#

import pytest
from segment import *

def test_segment_processing():
    cur_segment = Segment.create_segment(50, False, False, True, 4096, b"Lorem ipsum dolor sit amet, consectetur adipiscing elit. Nulla mattis urna metus. Pellentesque habitant morbi tristique senectus et netus et malesuada fames ac turpis egestas. Nulla lobortis a tortor a auctor. Vivamus efficitur blandit justo ac fermentum. Nunc gravida nisi elit, quis fringilla nulla vulputate ut. Fusce porttitor libero vitae leo euismod, vel sollicitudin ipsum consectetur. Quisque a massa metus. Etiam arcu dui, rutrum id sapien sit amet, scelerisque vestibulum nunc. Suspendisse vehicula lorem et scelerisque interdum. Nullam consectetur tincidunt scelerisque. Suspendisse posuere lorem ligula, a auctor justo interdum non. Donec sed semper velit. Morbi varius nisl in tincidunt euismod. Praesent urna nibh, egestas quis ullamcorper in, egestas quis ipsum. Maecenas auctor, erat eget dignissim facilisis, nisi libero maximus massa, eget ornare eros mi sit amet purus. Donec auctor mattis mi eget auctor.")
    assert Segment.process_segment(cur_segment) == (50, False, False, True, 4096, b"Lorem ipsum dolor sit amet, consectetur adipiscing elit. Nulla mattis urna metus. Pellentesque habitant morbi tristique senectus et netus et malesuada fames ac turpis egestas. Nulla lobortis a tortor a auctor. Vivamus efficitur blandit justo ac fermentum. Nunc gravida nisi elit, quis fringilla nulla vulputate ut. Fusce porttitor libero vitae leo euismod, vel sollicitudin ipsum consectetur. Quisque a massa metus. Etiam arcu dui, rutrum id sapien sit amet, scelerisque vestibulum nunc. Suspendisse vehicula lorem et scelerisque interdum. Nullam consectetur tincidunt scelerisque. Suspendisse posuere lorem ligula, a auctor justo interdum non. Donec sed semper velit. Morbi varius nisl in tincidunt euismod. Praesent urna nibh, egestas quis ullamcorper in, egestas quis ipsum. Maecenas auctor, erat eget dignissim facilisis, nisi libero maximus massa, eget ornare eros mi sit amet purus. Donec auctor mattis mi eget auctor.")