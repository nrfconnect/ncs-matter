/*
 * Copyright (c) 2026 Nordic Semiconductor ASA
 *
 * SPDX-License-Identifier: LicenseRef-Nordic-5-Clause
 */

#include "clusters/identify.h"

#include <app-common/zap-generated/ids/Clusters.h>
#include <lib/support/CodeUtils.h>

namespace Nrf::Matter
{

namespace
{
void RegisterIdentifyCluster(chip::EndpointId endpoint,
			     chip::app::RegisteredServerCluster<chip::app::Clusters::IdentifyCluster> & cluster)
{
	if (chip::app::CodegenDataModelProvider::Instance().Registry().Get(
		    { endpoint, chip::app::Clusters::Identify::Id }) != nullptr) {
		return;
	}

	CHIP_ERROR err = chip::app::CodegenDataModelProvider::Instance().Registry().Register(cluster.Registration());
	VerifyOrDie(err == CHIP_NO_ERROR);
}
} // namespace

IdentifyCluster::IdentifyCluster(chip::EndpointId endpoint, chip::app::Clusters::IdentifyDelegate &identifyDelegate,
				 chip::TimerDelegate &timerDelegate,
				 chip::app::Clusters::Identify::IdentifyTypeEnum identifyType)
	: mEndpointId(endpoint),
	  mDelegate(&identifyDelegate),
	  mIdentifyCluster(chip::app::Clusters::IdentifyCluster::Config(endpoint, timerDelegate)
				   .WithIdentifyType(identifyType)
				   .WithDelegate(mDelegate))
{
	RegisterIdentifyCluster(endpoint, mIdentifyCluster);
}

IdentifyCluster::IdentifyCluster(chip::EndpointId endpoint, bool isTriggerEffectEnabled,
				 std::function<void()> customIdentifyStopCallback,
				 chip::app::Clusters::Identify::IdentifyTypeEnum identifyType)
	: mEndpointId(endpoint),
	  mNrfDelegate(std::in_place, isTriggerEffectEnabled, customIdentifyStopCallback),
	  mDelegate(&(*mNrfDelegate)),
	  mIdentifyCluster(chip::app::Clusters::IdentifyCluster::Config(endpoint, mDefaultTimerDelegate)
				   .WithIdentifyType(identifyType)
				   .WithDelegate(mDelegate))
{
	RegisterIdentifyCluster(endpoint, mIdentifyCluster);
}

IdentifyCluster::~IdentifyCluster()
{
	RETURN_SAFELY_IGNORED chip::app::CodegenDataModelProvider::Instance().Registry().Unregister(
		&mIdentifyCluster.Cluster());
}

} // namespace Nrf::Matter
