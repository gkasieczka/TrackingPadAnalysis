#!/usr/bin/env python

"""
Program to populate the run info database
"""

###############################
# Imports
###############################

import sys

from RunInfo import RunInfo


###############################
# Get already saved runs
###############################

runs_filename = "runs.json"
RunInfo.load(runs_filename)


###############################
# Main work loop
###############################

last_run_number = max(RunInfo.runs.keys())

while True:
    
    last_run = RunInfo.runs[last_run_number]
    
    arguments = ["number", 
                 "begin_date",             
                 "begin_time",             
                 "end_time",               
                 "diamond",                
                 "data_type",              
                 "bias_voltage",           
                 "mask_time",              
                 "fsh13",                  
                 "fs11",                   
                 "rate_raw",               
                 "rate_ps",                
                 "rate_trigger",           
                 "events_nops",            
                 "events_ps",              
                 "events_trig",
                 "pedestal_run"]            

    dic = {}
    
    for argument_name in arguments:

        last_argument = getattr(last_run, argument_name)
        argument_type = type(last_argument)

        print "\n\nPlease enter {0}: (default = {1}). (or type reset or exit)".format(argument_name, last_argument)
        response = raw_input()

        if response == "":
            result = last_argument
        elif response == "reset":
            break
        elif response == "exit":
            sys.exit()
        else:
            result = argument_type(response)
            
        print "Using: ", result

        dic[argument_name] = result
    # End of loop over arguments

    # If we have a response for each parameter (did not break)
    if len(arguments) == len(dic.keys()):

        # Create a new object
        r = RunInfo(**dic)

        # Overwrite the run-list file
        RunInfo.dump(runs_filename)
        
        print "Created run {0} and updated {1}".format(r.number, runs_filename)
        
        last_run_number = r.number

# En dof main loop










