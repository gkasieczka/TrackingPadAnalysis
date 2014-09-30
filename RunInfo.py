#!/usr/bin/env python

"""
Class RunInfo for 2014 September PSI Testbeam Analysis.
"""


###############################
# Imports
###############################

import json

from Initializer import initializer


###############################
# MaskInfo
###############################

class RunInfo:

  # Dictionary with possible values for data_type field
  data_types = {
    0 : "DATA",
    1 : "PEDESTAL",
    2 : "VOLTAGESCAN",
    3 : "OTHER"
  }
  
  # Dictionary of all available runs
  #  -newly created objects register automatically
  #  -keys = run number
  runs= {}

  # initializer - a member variable is automatically created
  #  for each argument of the constructor
  @initializer
  def __init__(self, 
               number,                  # [int]
               begin_date,              # [string] (example: 2014-09-25)
               begin_time,              # [int] (example: 2030)
               end_time,                # [int] (example: 2035)
               diamond,                 # [string] (example: "S30")               
               data_type,               # [int] (key from data_types dictionary)
               bias_voltage,            # [int] (in Volts)
               mask_time,               # [int] (example: 2030)
               fsh13,                   # [int]
               fs11,                    # [int]
               rate_raw,                # [int] (Hz)
               rate_ps,                 # [int] (Hz, ps = prescaled)
               rate_trigger,            # [int] (Hz, used for triggering)
               events_nops,             # [int] (total events, nops = no prescale)
               events_ps,               # [int] (total events, ps = prescale)
               events_trig,             # [int] (total events, used for triggering)               
               pedestal = float('nan'), # [float] for data runs: which pedestal value to subtract
               comment = "",            # [string] free text
               # Next four parameters can be measured using TimingAlignment.py
               align_ev_pixel = -1,     # [int] pixel event for time-align
               align_ev_pad = -1,       # [int] pad event for time align
               time_offset = 0,         # float (seconds)
               time_drift = -1.9e-6):   # drift between pixel and pad clock

    # Add to runs dictionary
    RunInfo.runs[self.number] = self

  # End of __init__

  # Dump all RunInfos (the content of the runs dictionary)
  #  to a file using json
  @classmethod
  def dump(cls, filename):
    
    f = open(filename, "w")
    f.write(json.dumps(cls.runs, 
                       default=lambda o: o.__dict__, 
                       sort_keys=True, 
                       indent=4))
    f.close()
  # End of to_JSON
  
  # Read all RunInfos from a file and use to intialize objects
  @classmethod
  def load(cls, filename):
    
    # first get the dictionary from the file..
    f = open(filename, "r")
    data = json.load(f) 
    f.close()

    # ..then intialize the individual RunInfo objects from it
    for k,v in data.iteritems():
      RunInfo(**v)
    
  # End of to_JSON

# End of class RunInfo


# Run a simple test when called from command line
if __name__ == "__main__":

  # RunInfo(122, "2014-09-23", 2030, 2035, "S99", 0, -500, 1212, -1, 70, 500, 200, 200, 4500, 2500, 220)
  # RunInfo(125, "2014-09-25", 2031, 2055, "S99", 0, -500, 1212, -1, 70, 500, 200, 200, 4500, 2500, 220)
  # RunInfo.dump("runs.json")

  RunInfo.load("runs.json")
  print RunInfo.runs[125].diamond
