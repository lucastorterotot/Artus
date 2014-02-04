/* Copyright (c) 2013 - All Rights Reserved
 *   Thomas Hauth  <Thomas.Hauth@cern.ch>
 *   Joram Berger  <Joram.Berger@cern.ch>
 *   Dominik Haitz <Dominik.Haitz@kit.edu>
 */

#pragma once

#include "Artus/Core/interface/Cpp11Support.h"
#include "Artus/Core/interface/GlobalProducerBase.h"

#include "TestTypes.h"

typedef GlobalProducerBase<TestTypes> TestProducerBase;

class TestGlobalProducer: public TestProducerBase {
public:

	virtual std::string GetProducerId() {
		return "test_global_producer";
	}
	
	virtual bool ProduceGlobal(TestEvent const& event,
			TestProduct & globalProduct,
			TestGlobalSettings const& globalSettings) const ARTUS_CPP11_OVERRIDE {
		globalProduct.iGlobalProduct = event.iVal + 5 + globalSettings.GetOffset();
		return true;
	}
};