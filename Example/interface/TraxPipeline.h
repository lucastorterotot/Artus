/* Copyright (c) 2013 - All Rights Reserved
 *   Thomas Hauth  <Thomas.Hauth@cern.ch>
 *   Joram Berger  <Joram.Berger@cern.ch>
 *   Dominik Haitz <Dominik.Haitz@kit.edu>
 */

#pragma once

#include "Artus/Core/interface/EventPipeline.h"

#include "TraxTypes.h"

#include "TraxEventData.h"
#include "TraxMetaData.h"
#include "TraxPipelineSettings.h"

typedef EventPipeline<TraxTypes> TraxPipeline;
