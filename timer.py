#
# Columbia University - CSEE 4119 Computer Networks
# Assignment 2 - Mini Reliable Transport Protocol
#
# timer.py - helper class used by client API to track time elapsed
#

import threading
import time

class Timer:
    def __init__(self) -> None:
        """
        initialize the timer object for use by the client

        Set start time to current time and initialize lock for safe use by threads
        """
        self.last_time = time.time()
        self.lock = threading.Lock()
    
    def reset_timer(self):
        """
        Reset the time counted from to the current time
        """
        self.lock.acquire()
        self.last_time = time.time()
        self.lock.release()
    
    def should_resend(self):
        """
        Determine whether the client should resend a packet by counting time elapsed on the stopwatch

        return:
        boolean of whether more than 5 seconds has elapsed since setting the timer
        """
        self.lock.acquire()
        if (time.time() - self.last_time) > 5:
            out = True
        else:
            out = False
        self.lock.release()
        return out