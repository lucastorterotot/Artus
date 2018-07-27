# -*- coding: utf-8 -*-

import logging
import Artus.Utility.logger as logger
log = logging.getLogger(__name__)

import ROOT
import copy
import math
import os
import Artus.HarryPlotter.analysisbase as analysisbase


class Unfolding(analysisbase.AnalysisBase):
    """This module implements an unfolding procedure based on RooUnfold.
    
    Needed are
        - The histogram to be unfolded (nick)
        - MC gen-level histogram
        - MC reco-level histogram
        - 2D response matrix
        - path to libRooUnfold library
    
        optional: a variation parameter (default: 0) to vary the response matrix
            by e.g. one sigma up or down (variation = +1 or -1)
    
        see http://hepunx.rl.ac.uk/~adye/software/unfold/RooUnfold.html
    
        Example config = {
            'analysis_modules': ['Unfolding'],
            # configure input and output nicks:
            'unfolding': ['nick_data'],
            'unfolding_mc_gen': 'nick_mc_gen',
            'unfolding_mc_reco': 'mc_reco',
            'unfolding_new_nicks': ['data_unfolded'],
            'unfolding_responsematrix': 'nick_responsematrix',  # 2D histo, others are 1D
            # method and lib settings
            'unfolding_method': 'dagostini',
            'unfolding_iterations': 4,
            'libRooUnfold': '~/home/RooUnfold/libRooUnfold.so',
        }
    """
    
    def modify_argument_parser(self, parser, args):
        super(Unfolding, self).modify_argument_parser(parser, args)
    
        self.Unfolding_options = parser.add_argument_group(self.name() + " options")
        self.Unfolding_options.add_argument("--unfolding", type=str, nargs='*',
                help="List the nick(s) you want to unfold.")
        self.Unfolding_options.add_argument("--unfolding-responsematrix", type=str, nargs='*',
                help="List the nick(s) you want to use as unfolding responsematrix.")
        self.Unfolding_options.add_argument("--unfolding-mc-gen", type=str, nargs='*',
                help="List the nick(s) you want to use as unfolding mc gen.")
        self.Unfolding_options.add_argument("--unfolding-mc-reco", type=str, nargs='*',
                help="List the nick(s) you want to use as unfolding mc reco.")
        self.Unfolding_options.add_argument("--unfolding-variation", type=float, nargs='*', default=[0.],
                help="List the variations")
        self.Unfolding_options.add_argument("--unfolding-new-nicks", type=str, nargs='*', default="unfolded",
                help="List the nick(s) for the unfolded histograms.")
        self.Unfolding_options.add_argument("--libRooUnfold", type=str, default="",
                help="Location of libRooUnfold library file")
        self.Unfolding_options.add_argument("--unfolding-iterations", type=int, default=4,
                help="Number of iterations for unfolding")
        self.Unfolding_options.add_argument("--unfolding-regularization", type=int, default=1e-20,
                help="Parameter of regularization for unfolding")
        self.Unfolding_options.add_argument("--write-matrix", type=bool, default=False,
                help="Write the Covariance and Correlation Matrix in ROOT File")
        self.Unfolding_options.add_argument("--unfold-file", type=str, 
                help="Name of the file for the cov matrix if it should be written")
        self.Unfolding_options.add_argument("--unfolding-method", type=str, default="dagostini",
                choices=['dagostini', 'svd', 'binbybin', 'inversion','tunfold'],
                help="Method for unfolding. [Default: %(default)s]")
    
    def prepare_args(self, parser, plotData):
        super(Unfolding, self).prepare_args(parser, plotData)
        self.prepare_list_args(plotData, [
            "unfolding",
            "unfolding_responsematrix", 
            "unfolding_mc_gen",
            "unfolding_mc_reco",
            "unfolding_variation",
            "unfolding_new_nicks",
        ])
    
    def run(self, plotData=None):
        super(Unfolding, self).run(plotData)
    
        for data, matrix, gen, reco, variation, new_nick in zip(
                plotData.plotdict["unfolding"],
                plotData.plotdict["unfolding_responsematrix"],
                plotData.plotdict["unfolding_mc_gen"],
                plotData.plotdict["unfolding_mc_reco"],
                plotData.plotdict["unfolding_variation"],
                plotData.plotdict["unfolding_new_nicks"],
        ):
            unfolded_histo = self.do_unfolding(
                plotData.plotdict["root_objects"][matrix],
                plotData.plotdict["root_objects"][reco],
                plotData.plotdict["root_objects"][gen],
                plotData.plotdict["root_objects"][data],
                plotData.plotdict["unfolding_method"],
                plotData.plotdict["libRooUnfold"],
                variation,
                plotData.plotdict["write_matrix"],
                plotData.plotdict["unfold_file"],
                plotData.plotdict["unfolding_iterations"],
                plotData.plotdict["unfolding_regularization"]
            )
            plotData.plotdict["root_objects"][new_nick] = unfolded_histo
            plotData.plotdict["nicks"].append(new_nick)
    
    
    def do_unfolding(self, hResponse_input, hMeas, hTrue, hData, method, libRooUnfold_path, variation=0, write=False, unfold_file=None, iterations=4, regularization=1e-24):
        """return unfolded distribution"""
        ROOT.gSystem.Load(libRooUnfold_path)
    
        hResponse = copy.deepcopy(hResponse_input)
    
        # variation (+/- one sigma of response matrix entries)
        if variation is not 0:
            for x in range(hResponse.GetNbinsX()):
                for y in range(hResponse.GetNbinsY()):
                    hResponse.SetBinContent(x, y, hResponse.GetBinContent(x, y) + variation * hResponse.GetBinError(x, y))
    
        response = ROOT.RooUnfoldResponse(hMeas, hTrue, hResponse, hMeas.GetName(), hMeas.GetTitle())
    
        unfolding_methods = {
            'dagostini': ROOT.RooUnfoldBayes,  # iterative dagostini
            'svd': ROOT.RooUnfoldSvd,  # singular value decomposition
            'binbybin': ROOT.RooUnfoldBinByBin,  # bin-by-bin (simple correction factors)
            'inversion': ROOT.RooUnfoldInvert,  # inversion
            'tunfold': ROOT.RooUnfoldTUnfold,  # TUnfold
        }
    
        if method in ['dagostini']:
            unfold = unfolding_methods[method](response, hData, iterations)
        elif method in ['tunfold', 'svd']:
            unfold = unfolding_methods[method](response, hData, regularization)
        else:
            unfold = unfolding_methods[method](response, hData)
    
        if write == True:
            unfold.SetNToys(10000000)
            unfold.RunToy()
    
            resp_matrix = response.Mresponse()
            resp_matrix_error = response.Eresponse()
            cov_matrix = unfold.Ereco()
            unfold_matrix = unfold.Hreco()
            backfold_matrix = unfold.HrecoMeasured()
            
            out_file = ROOT.TFile(unfold_file[0], 'RECREATE')
            f = open(unfold_file[0].replace('.root','.txt'), 'w')
            reco_hist = hMeas.Clone("reco_hist")
            gen_hist = hTrue.Clone("gen_hist")
            resp_hist = hResponse.Clone("resp_hist")
            unfold_hist = hTrue.Clone("unfold_hist")
            backfold_hist = hMeas.Clone("backfold_hist")
            cov_hist = hResponse.Clone("cov_hist")
            corr_hist = hResponse.Clone("corr_hist")
            
            for x in xrange(1, resp_hist.GetNbinsX()+1):
                for y in xrange(1, resp_hist.GetNbinsY()+1):
                    resp_hist.SetBinContent(x, y, resp_matrix[x-1][y-1])
                    resp_hist.SetBinError(x, y, resp_matrix_error[x-1][y-1])
            
            for x in xrange(1,gen_hist.GetNbinsX()+1):
                unfold_hist.SetBinContent(x,unfold_matrix.GetBinContent(x))
                unfold_hist.SetBinError(x,unfold_matrix.GetBinError(x))
            for y in xrange(1,reco_hist.GetNbinsX()+1):
                backfold_hist.SetBinContent(y,backfold_matrix.GetBinContent(y))
                backfold_hist.SetBinError(y,backfold_matrix.GetBinError(y))
            
            for x in xrange(1, cov_hist.GetNbinsX()+1):
                for y in xrange(1, cov_hist.GetNbinsY()+1):
                    cov_hist.SetBinContent(x,y,cov_matrix[x-1][y-1])
                    try:
                        corr_hist.SetBinContent(x,y,cov_matrix[x-1][y-1]/(math.sqrt(cov_matrix[x-1][x-1]) * math.sqrt(cov_matrix[y-1][y-1])))
                    except ZeroDivisionError:
                        corr_hist.SetBinContent(x,y,0.)
                    f.write(str(corr_hist.ProjectionX().GetBinLowEdge(x))+" "+str(corr_hist.ProjectionX().GetBinLowEdge(x)+corr_hist.ProjectionX().GetBinWidth(x))+" "+str(corr_hist.ProjectionY().GetBinLowEdge(y))+" "+str(corr_hist.ProjectionY().GetBinLowEdge(y)+corr_hist.ProjectionY().GetBinWidth(y))+" "+ str(corr_hist.GetBinContent(x,y))+'\n')
                    cov_hist.SetBinError(x,y,0.)
                    corr_hist.SetBinError(x,y,0.)
            
            out_file.Write()
            out_file.Close()
        return unfold.Hreco()
