#!/usr/bin/env python

"""
Class MaskInfo for 2014 September PSI Testbeam Analysis.
"""


###############################
# Imports
###############################

import json

from Initializer import initializer


###############################
# MaskInfo
###############################

class MaskInfo:

  # Dictionary with possible values for data_type field
  data_types = {
    0 : "DATA",
    1 : "PEDESTAL",
    2 : "VOLTAGESCAN",
    3 : "OTHER"
  }
  

  # Dictionary of all available masks
  #  -newly created objects register automatically
  #  -keys are of the format "diamond-data_type-mask_time", ie:
  #    S30-DATA-2030
  masks = {}


  # Helper function: create_name
  # Create name (used as key for masks dict) from diamond, data_type and mask_time
  def create_name(self,
                  diamond,
                  data_type,
                  mask_time):
    return "{0}-{1}-{2}".format(diamond, 
                                MaskInfo.data_types[data_type], 
                                str(mask_time))
  # End of create_name
    

  # initializer - a member variable is automatically created
  #  for each argument of the constructor
  @initializer
  def __init__(self, 
               data_type,     # [int] (key from data_types dictionary)
               diamond,       # [string] (example: "S30")
               mask_time,     # [int] (example: 2030)
               min_row_roc0,  # [int]
               max_row_roc0,  # [int]
               min_col_roc0,  # [int]
               max_col_roc0,  # [int]
               min_row_roc4,  # [int]
               max_row_roc4,  # [int]
               min_col_roc4,  # [int]
               max_col_roc4,  # [int]
               min_x  = -2,   # [float]
               max_x  = -2,   # [float]
               min_y  = -2,   # [float]
               max_y  = -2):  # [float]

    # Add to masks dictionary
    name = self.create_name(self.diamond,
                            self.data_type,
                            self.mask_time)
    MaskInfo.masks[name] = self
  # End of __init__

  # Dump all MaskInfos (the content of the masks directory)
  #  to a file using json
  @classmethod
  def dump(cls, filename):
    
    f = open(filename, "w")
    f.write(json.dumps(cls.masks, 
                       default=lambda o: o.__dict__, 
                       sort_keys=True, 
                       indent=4))
    f.close()
  # End of to_JSON

# End of class MaskInfo  


test = MaskInfo(0, "S30", 2030, 0, 20, 0, 20, 0, 20, 0, 20)
MaskInfo.dump("test.json")
