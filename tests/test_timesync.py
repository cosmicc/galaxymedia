import os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import timesync

def test_timesync():
    result = timesync.checktime()
    assert result == 0
