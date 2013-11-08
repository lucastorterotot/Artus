/* Copyright (c) 2013 - All Rights Reserved
 *   Thomas Hauth  <Thomas.Hauth@cern.ch>
 *   Joram Berger  <Joram.Berger@cern.ch>
 *   Dominik Haitz <Dominik.Haitz@kit.edu>
 */

#pragma once

#include "Artus/Core/interface/Cpp11Support.h"
#include "Artus/Consumer/interface/ValueModifier.h"

#include "Artus/Consumer/interface/DrawHist1dConsumer.h"
#include "Artus/Consumer/interface/ProfileConsumerBase.h"

#include "TraxTypes.h"

#include "TraxPipelineSettings.h"
#include "TraxEventData.h"
#include "TraxProduct.h"

// filter
#include "PtFilter.h"

// consumer
#include "MeanPtConsumer.h"
#include "TraxNtupleConsumer.h"

class TraxPipelineInitializer: public PipelineInitilizerBase<TraxTypes> {
public:

	virtual void InitPipeline(TraxPipeline * pLine,
			TraxPipelineSettings const& pset) const ARTUS_CPP11_OVERRIDE
			{

		pLine->AddFilter(new PtFilter());
		pLine->AddConsumer(new MeanPtConsumer());

		typedef std::function<
				std::vector<float>(event_type const&, global_product_type const&,
						local_product_type const&)> ValueExtractLambda;
		typedef std::pair<ValueExtractLambda, ValueModifiers> ValueDesc;

		// define how to extract Pt and the range
		auto extractPtSim =
				[]( TraxEventData const& ev, TraxGlobalProduct const & gm, TraxLocalProduct const & lm )
				-> std::vector<float> {return {ev.m_floatPtSim};};
		auto PtSimValue = std::make_pair(extractPtSim,
				DefaultModifiers::getPtModifier(0.7, 1.3f));

		// extracts the value which has been corrected by a globalProducer
		auto extractPtSimCorrected =
				[]( TraxEventData const& ev, TraxGlobalProduct const & gm, TraxLocalProduct const & lm )
				-> std::vector<float> {return {gm.m_floatPtSim_corrected};};
		auto PtSimCorrectedValue = std::make_pair(extractPtSimCorrected,
				DefaultModifiers::getPtModifier(0.7, 1.3f));

		// define how to extract Theta and the range
		auto extractThetaSim =
				[]( TraxEventData const& ev, TraxGlobalProduct const & gm, TraxLocalProduct const & lm )
				-> std::vector<float> {return {ev.m_floatTheSim};};

		auto ThetaSimValue = std::make_pair(extractThetaSim,
				DefaultModifiers::getThetaModifier());


		BOOST_FOREACH(std::string id, pset.GetConsumer())
		{
			if (id == "quantities_all")
			{
				// plot Pt
				pLine->AddConsumer(
						new DrawHist1dConsumerBase<TraxTypes>("pt", PtSimValue));

				// plot Pt - corrected, from the global product
				pLine->AddConsumer(
						new DrawHist1dConsumerBase<TraxTypes>("pt_corr", PtSimCorrectedValue));


				// plot Theta
				pLine->AddConsumer(
						new DrawHist1dConsumerBase<TraxTypes>("theta", ThetaSimValue));

				// profile Pt over Theta
				pLine->AddConsumer(
						new ProfileConsumerBase<TraxTypes>("pt_over_theta",
							ThetaSimValue, PtSimValue));
			}
			else if (id == "ntuple")
				pLine->AddConsumer(new TraxNtupleConsumer);
		}

	}
};
