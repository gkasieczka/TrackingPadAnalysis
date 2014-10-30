# ##############################
# Imports
# ##############################

import os
import sys
import array
import math
from RunInfo import RunInfo
import time

try:
    import progressbar

    progressbar_loaded = True
except ImportError, e:
    print 'Module "progressbar" is installed, fall back to no progressbar'
    progressbar_loaded = False
    pass

import ROOT


# ##############################
# ensure_dir
# ##############################
def ensure_dir(f):
    print 'ensure dir: ', f
    if not f.endswith('/'):
        f = os.path.abspath(f)
        d = os.path.dirname(f)
        print 'ensure dir: ', f, d
        if not os.path.exists(d):
            print 'make dir', d
            os.makedirs(d)
    else:
        if not os.path.exists(f):
            os.makedirs(f)


# ##############################
# coordinate_to_box
# ##############################

def coordinate_to_box(x, y, min_x, max_x, min_y, max_y, n):
    """ Map x/y coordiantes into a n-times-n array of boxes.
    Return [x_box, y_box]
    Where x_box/y_box are the boxes-id to which the position is mapped.
    The x_xbox/y_box range goes from 0 to n-1.
    Return the number -1 instead of a list if one of the positions is outside the target range
    """

    # Make sure the input position is valid
    if (x < min_x) or (x > max_x) or (y < min_y) or (y > max_y):
        return -1

    # What is the range that should go into one box
    unit_length_x = 1.0 * (max_x - min_x) / n
    unit_length_y = 1.0 * (max_y - min_y) / n

    # Convert
    # For example 1 .. 4 into 4 boxes:
    # 0.0 .. 0.99999 into box 0
    # 1.0 .. 1.99999 into box 1
    # 2.0 .. 2.99999 into box 3
    # 3.0 .. 3.99999 into box 4
    x_box = int(math.floor((x - min_x) / unit_length_x))
    y_box = int(math.floor((y - min_y) / unit_length_y))

    return [x_box, y_box]


# ##############################
# Class: Diamond
# ##############################

class Diamond:
    """ Storage class for diamond position related variables

    Current memeber variables:
    name
    x_pos_min
    x_pos_max
    y_pos_min
    y_pos_max
    """

    diamonds = {}

    def __init__(self,
                 name,
                 x_pos_min,
                 x_pos_max,
                 y_pos_min,
                 y_pos_max):
        self.name = name
        self.x_pos_min = x_pos_min
        self.x_pos_max = x_pos_max
        self.y_pos_min = y_pos_min
        self.y_pos_max = y_pos_max

        Diamond.diamonds[name] = self

        # End __init__


# End of class Diamond

###############################
# Class: TimingAlignment
###############################
class TimingAlignment:
    def __init__(self, run, f_pixel, f_pad, branch_names):
        self.run = run
        self.action = 0
        self.output_dir = "./results"
        self.run_timing = None
        self.mask = None
        self.appendix = ''
        self.f_out = None
        self.out_branches = {}
        self.max_events = -1
        self.f_pad = f_pad
        self.f_pixel = f_pixel
        tree_pad = f_pad.Get("rec")
        tree_pixel = f_pixel.Get("time_tree")
        print "Read:"
        print "PAD Tree: ", tree_pad.GetEntries(), "entries"
        print "Pixel Tree: ", tree_pixel.GetEntries(), "entries"
        self.tree_pad = tree_pad
        self.tree_pixel = tree_pixel
        self.branch_names = branch_names
        self.histos = {}
        self.search_width_pixel = 6
        self.result_dir = "{0}/run_{1}/".format(self.output_dir, self.run)
        self.tree_out = None
        self.class_time = time.time()
        ensure_dir(self.result_dir)
        self.write_json = True
        ROOT.gROOT.SetBatch()
        ROOT.gErrorIgnoreLevel = 2001
        pass

    @staticmethod
    def pixel_to_pad_time(pixel_now, pixel_0, pad_now, pad_0, offset, slope, verbose=False):
        if False:
            print pixel_now, pixel_0, pad_now, pad_0, offset, slope
        # How many ticks have passed since first pixel time-stamp
        delta_pixel = pixel_now - pixel_0

        # Convert ticks to seconds (1 tick ~ 25 ns)
        delta_second = delta_pixel * 25e-9 + offset

        # Add time difference (in seconds) to initial pad time
        return pad_0 + delta_second + slope * (pad_now - pad_0)

    def set_run(self, run):
        self.run = run

    def set_action(self, action):
        self.action = action
        if action == 1:
            self.appendix = '_short'
        else:
            self.appendix = ''

    def set_branches(self):

        # Output ROOT File

        filename_out = "{0}/track_info{1}.root".format(self.result_dir, self.appendix)
        self.f_out = ROOT.TFile(filename_out, "recreate")

        # Output Tree
        self.tree_out = ROOT.TTree("track_info", "track_info")

        # Output branches
        self.out_branches = {}


        # Event Number (from pad)
        self.out_branches["n_pad"] = array.array('i', [0])
        self.tree_out.Branch('n_pad', self.out_branches["n_pad"], 'n_pad/I')

        # Matched Event Number (from pixel)
        self.out_branches["n_matched_pixel"] = array.array('i', [0])
        self.tree_out.Branch('n_matched_pixel', self.out_branches["n_matched_pixel"], 'n_matched_pixel/I')

        self.out_branches["t_pad"] = array.array('f', [0])
        self.tree_out.Branch('t_pad', self.out_branches["t_pad"], 't_pad/F')

        self.out_branches["t_pixel"] = array.array('f', [0])
        self.tree_out.Branch('t_pixel', self.out_branches["t_pixel"], 't_pixel/F')
        # Did we accept this event in the pixel+timing analysis
        # Possible reasons for rejection:
        #   - could not find event in the pixel stream
        #   - event found in the pixel stream but time difference too large
        #   - event matched but no track from pixels
        self.out_branches["accepted"] = array.array('i', [0])
        self.tree_out.Branch('accepted', self.out_branches["accepted"], 'accepted/I')

        # Track interesect with pad
        self.out_branches["track_x"] = array.array('f', [0.])
        self.out_branches["track_y"] = array.array('f', [0.])
        self.tree_out.Branch('track_x', self.out_branches["track_x"], 'track_x/F')
        self.tree_out.Branch('track_y', self.out_branches["track_y"], 'track_y/F')

        # Pad integral
        self.out_branches["integral50"] = array.array('f', [0.])
        self.tree_out.Branch('integral50', self.out_branches["integral50"], 'integral50/F')

        self.out_branches["calib_flag"] = array.array('i', [0])
        self.tree_out.Branch('calib_flag', self.out_branches["calib_flag"], 'calib_flag/I')

        self.out_branches["delta_pixel"] = array.array('i', [0])
        self.tree_out.Branch('delta_pixel', self.out_branches["delta_pixel"], 'delta_pixel/I')

        self.out_branches["hit_plane_bits"] = array.array('i', [0])
        self.tree_out.Branch('hit_plane_bits', self.out_branches["hit_plane_bits"], 'hit_plane_bits/I')

    def init_input_trees(self):
        self.set_events()
        # Get initial-times
        self.tree_pad.GetEntry(self.run_timing.align_ev_pad-1)
        self.initial_t_pad = getattr(self.tree_pad, self.branch_names["t_pad"])
        print 'Get Entry pad: ',self.run_timing.align_ev_pad,self.initial_t_pad

        self.tree_pixel.GetEntry(self.run_timing.align_ev_pixel)
        self.initial_t_pixel = getattr(self.tree_pixel, self.branch_names["t_pixel"])
        print 'Get Entry pixel: ',self.run_timing.align_ev_pixel,self.initial_t_pixel

        # Get final-times
        self.tree_pad.GetEntry(self.max_events-1)
        self.final_t_pad = getattr(self.tree_pad, self.branch_names["t_pad"])

        self.tree_pixel.GetEntry(self.max_events)
        self.final_t_pixel = getattr(self.tree_pixel, self.branch_names["t_pixel"])

    def initialize_analysis(self):
        RunInfo.load('runs.json')
        if self.run not in RunInfo.runs:
            raise Exception('cannot find run {run} in RunInfo json - Please add run first'.format(run=self.run))
        this_info = RunInfo.runs[self.run]
        print this_info
        self.run_timing = this_info
        this_mask = this_info.get_mask()
        self.diamond = Diamond(this_mask.diamond, this_mask.min_x, this_mask.max_x, this_mask.min_y, this_mask.max_y)
        self.set_branches()
        self.init_input_trees()
        pass

    def set_events(self):
        if self.action == 1:
            print "Doing Initial run - restricting events"
            self.max_events = min(25000, self.tree_pad.GetEntries() - 1)
        else:
            self.max_events = self.tree_pad.GetEntries() - 1

    def init_histogramms(self):
        self.histos = {}
        self.histos['h2'] = ROOT.TH2D("h2", "", 2000, 0, self.final_t_pad - self.initial_t_pad, 300, -0.01, 0.01)
        self.histos['h'] = ROOT.TH1D("h", "", 500, -0.007, 0.007)
        self.histos['h_delta_n'] = ROOT.TH1D("h_delta_n", "", 21, -10, 10)
        self.histos['h_calib_events'] = ROOT.TH2D("h_calib_events", "", 16, -0.5, 15.5, 2, -0.5, 1.5)

        self.histos['h_tracks'] = ROOT.TH2D("h_tracks", "", 100, -1, 1, 100, -1, 1)
        self.histos['h_integral'] = ROOT.TH3D("h_integral", "", 100, -1, 1, 100, -1, 1, 200, -1000, 1000)

        self.histos['h_tracks_zoom'] = ROOT.TH2D("h_tracks_zoom", "",
                                                 50,  # bins in x
                                                 self.diamond.x_pos_min,
                                                 self.diamond.x_pos_max,
                                                 50,  # bins in y
                                                 self.diamond.y_pos_min,
                                                 self.diamond.y_pos_max)

        self.histos['h_integral_zoom'] = ROOT.TH3D("h_integral_zoom", "",
                                                   50,  # bins in x
                                                   self.diamond.x_pos_min,
                                                   self.diamond.x_pos_max,
                                                   50,  # bins in y
                                                   self.diamond.y_pos_min,
                                                   self.diamond.y_pos_max,
                                                   200, -1000, 1000)

        n_boxes = 5  # How many boxes per side. Will use the boundaries of the
        # diamond and the coordinate_to_box function
        integral_box_matrix = []
        for x_pos in range(n_boxes):
            tmp_li = []
            for y_pos in range(n_boxes):
                name = 'integral_box_{0}_{1}'.format(x_pos, y_pos)
                if self.run_timing.bias_voltage > 0:
                    tmp_li.append(ROOT.TH1D(name, "", 200, -500, 200))
                else:
                    tmp_li.append(ROOT.TH1D(name, "", 200, -200, 500))
            # End of x-loop
            integral_box_matrix.append(tmp_li)
        self.histos['integral_box_matrix'] = integral_box_matrix

    def find_associated_pixel_event(self, i_pixel, time_pad, offset=0):
        """ Find the for a given pad time the pixel events which fits best timing wise in an
            range around a given pixel position

        :param i_pixel: educated guess for best pixel
        :param time_pad: time of pad event
        :return: best mached pixel: [i_pixel,delta_t_pixel-pad]
        """
        delta_ts = []
        xmin = i_pixel + offset - self.search_width_pixel
        xmax = i_pixel + offset + self.search_width_pixel
        for i_pixel_test in range(xmin, xmax):
            if i_pixel_test < 0:
                continue

            self.tree_pixel.GetEntry(i_pixel_test)
            time_pixel = getattr(self.tree_pixel, self.branch_names["t_pixel"])
            time_pixel_in_pad = self.pixel_to_pad_time(time_pixel,
                                                       self.initial_t_pixel,
                                                       time_pad,
                                                       self.initial_t_pad,
                                                       self.run_timing.time_offset,
                                                       self.run_timing.time_drift,
                                                       i_pixel_test == 0 and i_pixel == 0)
            delta_t = time_pixel_in_pad - time_pad
            delta_ts.append([i_pixel_test, delta_t, time_pixel_in_pad])
        # print delta_ts
        # raw_input()
        best_match = sorted(delta_ts, key=lambda x: abs(x[1]))[0]
        return best_match

    def find_first_alignment(self):
        c = ROOT.TCanvas()
        RunInfo.load('runs.json')

        max_align_pad = 10
        max_align_pixel = 80

        if self.run not in RunInfo.runs:
            raise Exception('cannot find run {run} in RunInfo json - Please add run first'.format(run=self.run))

        this_info = RunInfo.runs[self.run]
        try:
            this_mask = this_info.get_mask()
        except e:
            this_info.calibration_event_fraction = -5
            RunInfo.update_run_info(this_info)
            raise e
        self.mask = this_mask
        self.run_timing = this_info

        # We are going to select the alignment event with the lowest residual RMS
        # Make a list of triples: [pixel_event, pad_event, residual RMS]
        self.init_input_trees()
        index_pixel = 0
        index_pad = 1
        index_rms = 2
        li_residuals_rms = []

        found_good_match = False
        good_match_threshold = 0.000450  # RMS below 390 ns should be a good match
        n_events = 1000
        ensure_dir("{0}/aligning/".format(self.result_dir))
        self.search_width_pixel = 10
        # Loop over potential pad events for aligning:
        for i_align_pad in xrange(1, max_align_pad):
            if i_align_pad == 1 and len(li_residuals_rms) == 0:
                max_align_pixel = 80
            elif found_good_match:
                max_align_pixel = 20
            else:
                max_align_pixel = 40
            self.tree_pad.GetEntry(i_align_pad-1)
            self.initial_t_pad = getattr(self.tree_pad, self.branch_names["t_pad"])

            # Loop over potential pixel events for aligning:
            for i_align_pixel in xrange(max_align_pixel):
                if found_good_match and i_align_pixel >= 20:
                    break
                elif len(li_residuals_rms) and i_align_pixel >= 40:
                    break

                self.tree_pixel.GetEntry(i_align_pixel)
                self.initial_t_pixel = getattr(self.tree_pixel, self.branch_names["t_pixel"])
                name = "h_pad{i_pad}_pixel{i_pixel}".format(i_pad=i_align_pad, i_pixel=i_align_pixel)
                self.histos[name] = ROOT.TH1F(name, "", 1600, -0.04, 0.04)
                i_pixel = 0

                for i_pad in xrange(1, n_events):
                    self.tree_pad.GetEntry(i_pad-1)
                    time_pad = getattr(self.tree_pad, self.branch_names["t_pad"])

                    best_match = self.find_associated_pixel_event(i_pixel, time_pad, 1)
                    self.histos[name].Fill(best_match[1])

                    # Set the starting-value for the next iteration
                    # Our basis assumption is no-missing event
                    i_pixel = best_match[0] + 1
                    # End of loop over pad events

                self.histos[name].Draw()
                fname = "{0}/aligning/ipad_{1:02d}_ipixel_{2:02d}.".format(self.result_dir, i_align_pad,
                                                                              i_align_pixel)
                c.Print(os.path.abspath(fname+".pdf"))
                c.Print(os.path.abspath(fname+".png"))

                print "Pad Event {0:2d} / Pixel Event {1:2d}: Mean: {2:+2.6f} RMS:{3:+2.6f} Integral: {4:4.0f} | {5:3.0f} {6:3.0f}".format(i_align_pad,
                                                                                            i_align_pixel,
                                                                                            self.histos[name].GetMean(),
                                                                                            self.histos[name].GetRMS(),
                                                                                            self.histos[name].Integral(),
                                                                                            self.histos[name].GetBinContent(0),
                                                                                            self.histos[name].GetBinContent(self.histos[name].GetNbinsX()+1))

                # Make sure we have enough events actually in the histogram
                if self.histos[name].Integral() > 900:
                    li_residuals_rms.append(
                        [i_align_pixel, i_align_pad, self.histos[name].GetRMS(), self.histos[name].GetMean()])
                    # if we found a good match we can stop
                    if self.histos[name].GetRMS() < good_match_threshold:
                        found_good_match = True
                        if not found_good_match:
                            print 'found good match'
                        # break

                        # End of loop over pixel alignment events

                        # if found_good_match:
                        #     break
                        # End of loop over pad alignment events
        if len(li_residuals_rms) == 0:
            raise Exception('did not find any candidate')

        print sorted(li_residuals_rms, key=lambda x: abs(x[index_rms]))
        best_i_align_pixel = sorted(li_residuals_rms, key=lambda x: abs(x[index_rms]))[0][index_pixel]
        best_i_align_pad = sorted(li_residuals_rms, key=lambda x: abs(x[index_rms]))[0][index_pad]


        print "Best pad / pixel event for alignment: ", best_i_align_pad, best_i_align_pixel
        self.run_timing.align_ev_pixel = best_i_align_pixel
        self.run_timing.align_ev_pad = best_i_align_pad
        self.run_timing.print_info()
        if self.write_json:
            RunInfo.update_run_info(self.run_timing)
        pass

    def loop(self):
        i_pixel = self.run_timing.align_ev_pixel
        bar = None
        if progressbar_loaded:
            widgets = [progressbar.Bar('=', ' [', ']'), ' ', progressbar.Percentage()]
            # bar = progressbar.ProgressBar("Analyzed Events:",maxval=max_events, widgets=widgets).start()
            bar = progressbar.ProgressBar(maxval=self.max_events, widgets=widgets, term_width=50).start()

        for i_pad in xrange(self.run_timing.align_ev_pad,self.max_events):
            if bar:
                bar.update(i_pad)
            else:
                if i_pad % 1000 == 0: print "{0} / {1}".format(i_pad, self.max_events)

            self.tree_pad.GetEntry(i_pad-1)
            time_pad = getattr(self.tree_pad, self.branch_names["t_pad"])

            best_match = self.find_associated_pixel_event(i_pixel, time_pad)
            delta_pixel = -1* i_pixel
            i_pixel = best_match[0]
            delta_pixel += i_pixel
            self.tree_pixel.GetEntry(i_pixel)

            # Check if we are happy with the timing
            # (residual below 1 ms)
            is_correctly_matched = abs(best_match[1]) < 0.001
            calib_flag = getattr(self.tree_pad, self.branch_names["calib_flag_pad"])
            integral50 = getattr(self.tree_pad, self.branch_names["integral_50_pad"])
            time_pixel_in_pad = best_match[2]

            if is_correctly_matched:
                self.out_branches["accepted"][0] = 1
            hit_plane_bits = getattr(self.tree_pixel, self.branch_names["plane_bits_pixel"])
            track_x = getattr(self.tree_pixel, self.branch_names["track_x"])
            track_y = getattr(self.tree_pixel, self.branch_names["track_y"])
            self.out_branches['n_matched_pixel'][0] = i_pixel
            #     # print i_pixel
            # else:
            #     hit_plane_bits = -1
            #     track_x = -999
            #     track_y = -999
            #     self.out_branches["accepted"][0] = 0
            #     self.out_branches['n_matched_pixel'][0] = -1

            self.out_branches["n_pad"][0] = getattr(self.tree_pad, self.branch_names["n_pad"])
            self.out_branches["t_pad"][0] = time_pad
            self.out_branches["t_pixel"][0] = time_pixel_in_pad
            self.out_branches["track_x"][0] = track_x
            self.out_branches["track_y"][0] = track_y
            self.out_branches["integral50"][0] = integral50
            self.out_branches["calib_flag"][0] = calib_flag
            self.out_branches["hit_plane_bits"][0] = hit_plane_bits
            self.out_branches['delta_pixel'][0] = delta_pixel
            self.tree_out.Fill()
            self.histos['h_delta_n'].Fill(best_match[0] - i_pixel + 1)
            self.histos['h'].Fill(best_match[1])
            self.histos['h2'].Fill(time_pad - self.initial_t_pad, best_match[1])

            if is_correctly_matched:
                self.histos['h_calib_events'].Fill(hit_plane_bits, calib_flag)
                self.histos['h_tracks'].Fill(track_x, track_y)
                self.histos['h_tracks_zoom'].Fill(track_x, track_y)
                self.histos['h_integral'].Fill(track_x, track_y, integral50)
                self.histos['h_integral_zoom'].Fill(track_x, track_y, integral50)
                n_boxes = 5
                ret = coordinate_to_box(track_x,
                                        track_y,
                                        self.diamond.x_pos_min,
                                        self.diamond.x_pos_max,
                                        self.diamond.y_pos_min,
                                        self.diamond.y_pos_max,
                                        n_boxes)
                if ret != -1:
                    x_box = ret[0]
                    y_box = ret[1]
                    self.histos['integral_box_matrix'][x_box][y_box].Fill(integral50)


    def save_histograms(self):
        c = ROOT.TCanvas()
        self.histos['h'].GetXaxis().SetTitle("t_{pixel} - t_{pad} [s]")
        self.histos['h'].GetYaxis().SetTitle("Events")
        self.histos['h'].Draw()
        c.Print("{0}/residual{1}.pdf".format(self.result_dir, self.appendix))

        # print h2, c
        fun = ROOT.TF1("fun", "[0]+[1]*x")
        self.histos['h2'].Fit(fun, "Q", "")
        self.histos['h2'].GetYaxis().SetTitleOffset(1.9)
        self.histos['h2'].GetXaxis().SetTitle("t_{pad} [s]")
        self.histos['h2'].GetYaxis().SetTitle("t_{pixel} - t_{pad} [s]")
        self.histos['h2'].Draw()
        c.Print("{0}/time{1}.pdf".format(self.result_dir, self.appendix))
        c.Print("{0}/time{1}.png".format(self.result_dir, self.appendix))
        c.Print("{0}/time{1}.root".format(self.result_dir, self.appendix))

        self.run_timing.time_offset -= fun.GetParameter(0)
        self.run_timing.time_drift -= fun.GetParameter(1)

        c.SetLogy(1)
        self.histos['h_delta_n'].Draw()
        c.Print("{0}/delta_n{1}.pdf".format(self.result_dir, self.appendix))
        c.SetLogy(0)

        ROOT.gStyle.SetOptStat(0)
        c.SetLogz(1)
        self.histos['h_calib_events'].GetXaxis().SetTitle("Pixel Plane Hit Bit")
        self.histos['h_calib_events'].GetYaxis().SetTitle("Pad Calibration Flag")
        self.histos['h_calib_events'].GetYaxis().SetTitleOffset(1.5)
        self.histos['h_calib_events'].Draw("COLZTEXT")
        c.Print("{0}/calib_events{1}.pdf".format(self.result_dir, self.appendix))
        c.Print("{0}/calib_events{1}.root".format(self.result_dir, self.appendix))

        ROOT.gStyle.SetOptStat(0)
        c.SetLogz(1)
        self.histos['h_tracks'].GetXaxis().SetTitle("Pad position x [cm]")
        self.histos['h_tracks'].GetYaxis().SetTitle("Pad position y [cm]")
        self.histos['h_tracks'].GetYaxis().SetTitleOffset(1.5)
        self.histos['h_tracks'].Draw("COLZ")
        c.Print("{0}/tracks{1}.pdf".format(self.result_dir, self.appendix))

        ROOT.gStyle.SetOptStat(0)
        c.SetLogz(1)
        self.histos['h_tracks_zoom'].GetXaxis().SetTitle("Pad position x [cm]")
        self.histos['h_tracks_zoom'].GetYaxis().SetTitle("Pad position y [cm]")
        self.histos['h_tracks_zoom'].GetYaxis().SetTitleOffset(1.5)
        self.histos['h_tracks_zoom'].Draw("COLZ")
        c.Print("{0}/tracks_zoom{1}.pdf".format(self.result_dir, self.appendix))

        ROOT.gStyle.SetOptStat(0)
        c.SetLogz(0)
        proj = self.histos['h_integral'].Project3DProfile("yx")
        proj.SetTitle("")
        proj.GetXaxis().SetTitle("Pad Position x [cm]")
        proj.GetYaxis().SetTitle("Pad Position y [cm]")
        proj.GetXaxis().SetTitleOffset(1.2)
        proj.GetYaxis().SetTitleOffset(1.5)

        proj.Draw("COLZ")
        ensure_dir('{0}/integrals/'.format(self.result_dir))
        c.Print("{0}/integrals/integral{1}_fullrange.pdf".format(self.result_dir, self.appendix))

        ROOT.gStyle.SetOptStat(0)
        c.SetLogz(0)
        proj_zoom = self.histos['h_integral_zoom'].Project3DProfile("yx")
        proj_zoom.SetTitle("")
        proj_zoom.GetXaxis().SetTitle("Pad Position x [cm]")
        proj_zoom.GetYaxis().SetTitle("Pad Position y [cm]")
        proj_zoom.GetXaxis().SetTitleOffset(1.2)
        proj_zoom.GetYaxis().SetTitleOffset(1.5)

        proj_zoom.Draw("COLZ")
        c.Print("{0}/integrals/integral{1}_zoom_fullrange.pdf".format(self.result_dir, self.appendix))

        if self.run_timing.bias_voltage > 0:
            proj.SetMinimum(-550)
            proj.SetMaximum(50)

            proj_zoom.SetMinimum(-550)
            proj_zoom.SetMaximum(50)
        else:
            proj.SetMinimum(-50)
            proj.SetMaximum(500)

            proj_zoom.SetMinimum(-50)
            proj_zoom.SetMaximum(500)

        proj.Draw("COLZ")
        c.Print("{0}/integral{1}.pdf".format(self.result_dir, self.appendix))

        proj_zoom.Draw("COLZ")
        c.Print("{0}/integral_zoom{1}.pdf".format(self.result_dir, self.appendix))
        for x_pos in range(len(self.histos['integral_box_matrix'])):
            for y_pos in range(len(self.histos['integral_box_matrix'][x_pos])):
                fun = ROOT.TF1("", "gaus")
                self.histos['integral_box_matrix'][x_pos][y_pos].Fit(fun,"Q")
                print "XXX X: {0} Y: {1} Mean: {2:2.2f} RMS {3:2.2f}".format(x_pos,
                                                                             y_pos,
                                                                             fun.GetParameter(1),
                                                                             fun.GetParameter(2))
                self.histos['integral_box_matrix'][x_pos][y_pos].Draw()
                c.Print("{0}/integrals/1d_integral_x_{1}_y_{2}{3}.pdf".format(self.result_dir, x_pos, y_pos,
                                                                              self.appendix))
                c.Print("{0}/integrals/1d_integral_x_{1}_y_{2}{3}.png".format(self.result_dir, x_pos, y_pos,
                                                                              self.appendix))
        self.f_out.Write()
        total_calib_events = 0
        for i in range(1, 17):
            total_calib_events += int(self.histos['h_calib_events'].GetBinContent(i, 2))
        calibEventsNoHit = int(self.histos['h_calib_events'].GetBinContent(1, 2))
        calibEventsFullHit = int(self.histos['h_calib_events'].GetBinContent(16, 2))

        print 'There are \n\t  {:6d} calibration events ' \
              'from which\n\t' \
              '- {:6d} have Pixel Bit  0 [no Hit]\n\t' \
              '- {:6d} have Pixel Bit 15 [all Hit]'.format(total_calib_events,
                                                           calibEventsNoHit,
                                                           calibEventsFullHit)
        if total_calib_events > 0:
            fraction = float(calibEventsNoHit) / float(total_calib_events) * 100.
        else:
            fraction = -2.0
        print 'Run {:3d}: The fraction of correctly assign events is {:6.2f}% '.format(self.run,fraction)
        self.run_timing.calibration_event_fraction = fraction
        self.run_timing.time_pad_data = self.f_pad.GetCreationDate().Convert()
        self.run_timing.time_pixel_data = self.f_pixel.GetCreationDate().Convert()
        self.run_timing.time_timing_alignment = int(self.class_time)


    def analyse(self):
        self.initialize_analysis()
        self.init_histogramms()

        self.loop()
        self.save_histograms()

        if self.action != 0:
            if self.write_json:
                RunInfo.update_run_info(self.run_timing)
            pass