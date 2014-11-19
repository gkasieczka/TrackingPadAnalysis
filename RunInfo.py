#!/usr/bin/env python

"""
Class RunInfo for 2014 September PSI Testbeam Analysis.
"""


# ##############################
# Imports
###############################

import json
import types as t

import ROOT
from Initializer import initializer
from MaskInfo import MaskInfo
from DataTypes import data_types
import ConfigParser
# import portalocker
from lockfile import LockFile
import os
import math
import time

def irr(diamond):
    if diamond in ['IIa-2', 'IIa-3', 'S30']:
        return 'n-irr.'
    if diamond in ['S129', 'IIa-1', 'IIa-5']:
        return 'non-irr.'
    if diamond in ['S125', 'S66']:
        return 'p-irr.'
    else:
        return 'none'


def signum(x):
    return (x > 0) - (x < 0)

parser = ConfigParser.ConfigParser()
parser.read('TimingAlignment.cfg')
MaskInfo.load(parser.get('JSON','masks'))

###############################
# MaskInfo
###############################

class RunInfo:

    # Dictionary of all available runs
    #  -newly created objects register automatically
    #  -keys = run number
    runs = {}
    locked = False

    # initializer - a member variable is automatically created
    #  for each argument of the constructor
    @initializer
    def __init__(self,
                 number,  # [int]
                 begin_date,  # [string] (example: 2014-09-25)
                 begin_time,  # [int] (example: 2030)
                 end_time,  # [int] (example: 2035)
                 diamond,  # [string] (example: "S30")
                 data_type,  # [int] (key from data_types dictionary)
                 bias_voltage,  # [int] (in Volts)
                 mask_time,  # [int] (example: 2030)
                 fsh13,  # [int]
                 fs11,  # [int]
                 rate_raw,  # [int] (Hz)
                 rate_ps,  # [int] (Hz, ps = prescaled)
                 rate_trigger,  # [int] (Hz, used for triggering)
                 events_nops,  # [int] (total events, nops = no prescale)
                 events_ps,  # [int] (total events, ps = prescale)
                 events_trig,  # [int] (total events, used for triggering)
                 pedestal_run,  # [int] run from which to take pedestal information
                 #         (set to -1 for pedestal runs or if no pedestal run is available)
                 # test_campaign="PSI_Sept14",
                 test_campaign="PSI_July14",
                 # [str] Which testbeam campaign are the data from
                 pedestal=float('nan'),  # [float] for data runs: which pedestal value to subtract
                 pedestal_sigma=float('nan'),
                 comment="",  # [string] free text
                 # Next four parameters can be measured using TimingAlignment.py
                 align_ev_pixel=-1,  # [int] pixel event for time-align
                 align_ev_pad=-1,  # [int] pad event for time align
                 time_offset=0.,  # float (seconds)
                 time_drift=-1.9e-6,  # drift between pixel and pad clock
                 calibration_event_fraction=-1.,
                 time_pad_data=-1,
                 time_pixel_data=-1,
                 time_timing_alignment=-1,
                 time_analyse=-1

                 ): # fraction of correctly matched calibration events

        # Validate
        assert (type(number) is t.IntType and 0 < number < 1000), "Invalid run number"
        assert (type(begin_date) is t.StringType or type(begin_date) is t.UnicodeType ), "Invalid begin_date"
        assert (type(begin_time) is t.IntType and (
        0 <= begin_time and begin_time / 100 < 24 and begin_time % 100 < 60) or begin_time == -1), "Invalid begin_time"
        assert (type(end_time) is t.IntType and (
        0 <= end_time and end_time / 100 < 24 and end_time % 100 < 60) or end_time == -1), "Invalid end_time"
        assert (type(diamond) is t.StringType or type(diamond) is t.UnicodeType), "Invalid diamond"
        assert (data_type in data_types.keys()), "Invalid data_type"
        assert (type(bias_voltage) is t.IntType and -2000 < bias_voltage < 2000)
        assert (type(mask_time) is t.IntType and 0 <= mask_time), "Invalid mask_time"
        assert (type(fsh13) is t.IntType and -200 <= fsh13 <= -1), "Invalid fsh13"
        assert (type(fs11) is t.IntType and 0 < fs11 <= 200), "Invalid fs11"
        assert (type(rate_raw) is t.IntType), "Invalid rate_raw"
        assert (type(rate_ps) is t.IntType), "Invalid rate_ps"
        assert (type(rate_trigger) is t.IntType), "Invalid rate_trigger"
        assert (type(events_nops) is t.IntType), "Invalid events_nops"
        assert (type(events_ps) is t.IntType), "Invalid events_ps"
        assert (type(events_trig) is t.IntType), "Invalid events_trig"
        assert (type(pedestal_run) is t.IntType), "Invalid pedestal_run"
        assert (type(pedestal) is t.FloatType), "Invalid pedestal"
        assert (type(comment) is t.StringType or type(comment) is t.UnicodeType), "Invalid comment"
        assert (type(align_ev_pixel) is t.IntType), "Invalid align_ev_pixel"
        assert (type(align_ev_pad) is t.IntType), "Invalid align_ev_pad"
        assert (type(time_offset) is t.FloatType), "Invalid time_offset"
        assert (type(time_drift) is t.FloatType), "Invalid time_drift"
        assert (type(calibration_event_fraction) is t.FloatType),"invalid calibration_event_fraction \"{0}\"".format(calibration_event_fraction)

        # Add to runs dictionary
        RunInfo.runs[self.number] = self



    def get_mask_key(self):
        key = MaskInfo.create_name(self.diamond, signum(self.bias_voltage), self.data_type, self.mask_time)
        return key

    def get_mask(self):
        #diamond, bias_sign,MaskInfo.data_types[data_type],str(mask_time))
        key = self.get_mask_key()
        if key in MaskInfo.masks:
            return MaskInfo.masks[key]
        else:
            raise Exception('cannot find key {key} in {keys}'.format(key=key, keys=MaskInfo.masks.keys()))

    def print_info(self):
        print 'RunTiming({0}, {1}, {2}, {3}, {4}, "{5}", {6})'.format(self.number,
                                                                          self.time_offset,
                                                                          self.time_drift,
                                                                          self.align_ev_pixel,
                                                                          self.align_ev_pad,
                                                                          self.diamond,
                                                                          self.bias_voltage)

    def get_rate(self):
        rates = {
            "PSI_Sept14":{
                (1,70): 4000,
                (2,70): 10000,
                (10,70): 55000,
                (50,80): 620000,
                (50,120): 2000000
            },
            "PSI_July14":{
                (2,70): 10000,
                (10,70): 55000,
                (50,80): 620000,
                (50,120): 2000000
            }
        }
        fsh13 = abs(self.fsh13)
        fs11 = abs(self.fs11)
        if not self.test_campaign in rates:
            return 1
        if not (fsh13,fs11) in rates[self.test_campaign]:
            return 2
        return rates[self.test_campaign][(fsh13,fs11)]

    def get_rate_string(self):
        rate = self.get_rate()
        factor = int(math.log10(rate))/3*3
        factor_strings = {0:'',3:'k',6:'M',9:'G',12:'P'}
        rate = rate/10**factor
        return '%3.1f %sHz/cm^{2}'%(rate,factor_strings[factor])
    
    def get_voltage_string(self,unit=True):
        bias = self.bias_voltage
        if bias <0: 
            retVal = 'neg' 
            bias *= -1
        else:
            retVal = 'pos' 
        if unit:
            retVal+='%04d'%bias
            retVal+='V'
        else:
            retVal+='%d'%bias
        return retVal
    

    def addDiamondInfo(this,x1, y1, x2, y2 ):
        pave = ROOT.TPaveText(x1, y1, x2, y2, 'NDC')
        pave.SetTextAlign(12)
        pave.SetTextFont(82)
        pave.SetFillColor(0)
        pave.AddText(this.diamond+'\t '+irr(this.diamond))
        pave.AddText('bias: %+5d V'%this.bias_voltage)
        # pave.AddText('rate: '+rate)
        pave.AddText('rate: %s' %(this.get_rate_string()))
        pave.SetShadowColor(0)
        pave.SetBorderSize(0)
        pave.SetTextFont(42)
        pave.SetTextSize(0.04)
        return pave

    # End of __init__
    @staticmethod
    def update_timing(run, align_ev_pixel, align_ev_pad, time_offset, time_drift):
        RunInfo.runs[run].align_ev_pixel = align_ev_pixel
        RunInfo.runs[run].align_ev_pad = align_ev_pad
        RunInfo.runs[run].time_offset = time_offset
        RunInfo.runs[run].time_drift = time_drift

    @staticmethod
    def update_run_info(run_timing):
        # run_timing.print_info()
        print 'save to json: ',run_timing.number
        RunInfo.load(parser.get('JSON','runs'))
        RunInfo.runs[run_timing.number] = run_timing
        # RunInfo.update_timing(run_timing.run, run_timing.align_pixel, run_timing.align_pad, run_timing.offset,
        #                       run_timing.slope)
        RunInfo.dump(parser.get('JSON','runs'))

    # Dump all RunInfos (the content of the runs dictionary)
    #  to a file using json
    @classmethod
    def dump(cls, filename):
        lock = LockFile(filename)
        print 'write new json file, is locked: ',lock.is_locked(),'\t'
        try:
            lock.acquire(timeout=60)    # wait up to 60 seconds
        except LockTimeout:
            print "Cannot acquire file, break lock:", lock.path,'\t',
            lock.break_lock()
            lock.acquire()
        # with lock:
        f = open(filename, "w")
        # portalocker.lock(file, portalocker.LOCK_EX)
        # portalocker.lock(file, portalocker.LOCK_SH)
        f.write(json.dumps(cls.runs,
                           default=lambda o: o.__dict__,
                           sort_keys=True,
                           indent=4))
        f.close()
        lock.release()
        print 'DONE WITH WRITING'

    # End of to_JSON

    # Read all RunInfos from a file and use to intialize objects
    @classmethod
    def load(cls, filename):
        lock = LockFile(filename)
        i = 0
        while lock.is_locked():
            i+=1
            time.sleep(.01)
            if i%100==0:
                print 'waiting to be unlocked'
        # first get the dictionary from the file..
        f = open(filename, "r")
        data = json.load(f)
        f.close()

        # ..then intialize the individual RunInfo objects from it
        for k, v in data.iteritems():
            RunInfo(**v)

            # End of to_JSON

# End of class RunInfo

if __name__ == "__main__":
    parser = ConfigParser.ConfigParser()
    parser.read('TimingAlignment.cfg')
    fname = parser.get('JSON','runs')
    if os.path.isfile(fname):
        print 'Load RunInfo: ', fname
        RunInfo.load(fname)
        lock = LockFile(fname)
        print 'is_locked:',lock.is_locked()
        # RunInfo.dump(fname)
        runs = [461, 622, 663] 
        for run in runs:
            print run,RunInfo.runs[run].get_mask_key()
            try:
                RunInfo.runs[run].get_mask()
                print 'OK'
            except Exception as e:
                print 'Failed',e
                pass
