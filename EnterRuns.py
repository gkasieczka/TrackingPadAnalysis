#!/usr/bin/env python

"""
Program to populate the run info database
"""

###############################
# Imports
###############################
from DataTypes import data_types
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
july_entered_runs = []
for entry in RunInfo.runs:
    if getattr(RunInfo.runs[entry],"test_campaign") == "PSI_July14":
        july_entered_runs.append(entry)
#last_run_number = max(RunInfo.runs.keys())
last_run_number = max(july_entered_runs)

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


    i = 0
    while i < len(arguments):
        argument_name = arguments[i]

        last_argument = getattr(last_run, argument_name)
        if argument_name == 'number':
            last_argument += 1
        if argument_name == 'pedestal_run' and dic.get('data_type',0) == 1:
            last_argument = dic['number']
        argument_type = type(last_argument)

        print "\nEnter {0}: (default = {1}). (or type back, reset or exit)".format(argument_name, last_argument)
        if argument_name == "data_type":
            for k in sorted(data_types.keys()):
                print "{0}: {1}".format(k, data_types[k])

        if argument_name == "pedestal_run":
            print "run from which to take pedestal information"
            print  "(set to -1 for pedestal runs or if no pedestal run is available)"

        response = raw_input()

        if response == "reset":
            i = 0
        elif response == "exit":
            sys.exit()
        elif response == 'back':
            if i > 0:
                i -= 1
        else:
            i += 1
            if response == "":
                result = last_argument
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
        RunInfo.update_run_info(r)
        
        print "Created run {0} and updated {1}".format(r.number, runs_filename)
        
        last_run_number = r.number

# En dof main loop










