/*
 * Copyright (c) 2023 Nordic Semiconductor ASA
 *
 * SPDX-License-Identifier: LicenseRef-Nordic-5-Clause
 */

#include "binding_handler.h"

#include <zephyr/logging/log.h>

LOG_MODULE_DECLARE(app, CONFIG_CHIP_APP_LOG_LEVEL);

using namespace chip;
using namespace chip::app;
using namespace chip::app::Clusters;

namespace Nrf::Matter
{
void BindingHandler::Init()
{
	InitInternal();
}

void BindingHandler::RunBoundClusterAction(BindingData *bindingData)
{
	VerifyOrReturn(bindingData != nullptr, LOG_ERR("Invalid binding data"));
	VerifyOrReturn(bindingData->InvokeCommandFunc != nullptr, LOG_ERR("No valid InvokeCommandFunc assigned"););

	CHIP_ERROR err =
		DeviceLayer::PlatformMgr().ScheduleWork(DeviceWorkerHandler, reinterpret_cast<intptr_t>(bindingData));
	VerifyOrReturn(err == CHIP_NO_ERROR, LOG_ERR("ScheduleWork failed: %" CHIP_ERROR_FORMAT, err.Format()));
}

void BindingHandler::OnInvokeCommandSucces()
{
	LOG_DBG("Binding command applied successfully!");
}

void BindingHandler::OnInvokeCommandFailure(BindingData &bindingData, CHIP_ERROR Error)
{
	if (Error == CHIP_ERROR_TIMEOUT && !bindingData.CaseSessionRecovered) {
		LOG_INF("Response timeout for invoked command, trying to recover CASE session.");

		/* The binding manager takes the ownership of the context passed to
		 * NotifyBoundClusterChanged and releases it using DeviceContextReleaseHandler, so a new
		 * object must be allocated instead of reusing the one owned by the invoke callback.
		 */
		BindingData *recoveryData = Platform::New<BindingData>();
		VerifyOrReturn(recoveryData != nullptr, LOG_ERR("Cannot allocate binding data for CASE recovery"));
		*recoveryData = bindingData;

		/* Set flag to not try recover session multiple times. */
		recoveryData->CaseSessionRecovered = true;

		/* Establish new CASE session and retrasmit command that was not applied. */
		CHIP_ERROR error = Binding::Manager::GetInstance().NotifyBoundClusterChanged(
			recoveryData->EndpointId, recoveryData->ClusterId, static_cast<void *>(recoveryData));

		if (CHIP_NO_ERROR != error) {
			LOG_ERR("NotifyBoundClusterChanged failed due to: %" CHIP_ERROR_FORMAT, error.Format());
		}
	} else {
		LOG_ERR("Binding command was not applied! Reason: %" CHIP_ERROR_FORMAT, Error.Format());
	}
}

void BindingHandler::DeviceChangedCallback(const Binding::TableEntry &binding, OperationalDeviceProxy *deviceProxy,
					   void *context)
{
	VerifyOrReturn(context != nullptr, LOG_ERR("Invalid context for device handler"));
	BindingData *data = static_cast<BindingData *>(context);

	if (binding.type == Binding::MATTER_MULTICAST_BINDING) {
		if (data->IsGroup.HasValue() && !data->IsGroup.Value()) {
			return;
		}

		data->InvokeCommandFunc(binding, nullptr, *data);
	} else if (binding.type == Binding::MATTER_UNICAST_BINDING) {
		if (data->IsGroup.HasValue() && data->IsGroup.Value()) {
			return;
		}

		data->InvokeCommandFunc(binding, deviceProxy, *data);
	}
}

void BindingHandler::DeviceContextReleaseHandler(void *context)
{
	VerifyOrDie(context != 0);

	Platform::Delete(static_cast<BindingData *>(context));
}

void BindingHandler::InitInternal()
{
	LOG_INF("Initialize binding Handler");
	auto &server = Server::GetInstance();
	if (CHIP_NO_ERROR !=
	    Binding::Manager::GetInstance().Init(
		    { &server.GetFabricTable(), server.GetCASESessionManager(), &server.GetPersistentStorage() })) {
		LOG_ERR("BindingHandler::InitInternal failed");
	}

	Binding::Manager::GetInstance().RegisterBoundDeviceChangedHandler(DeviceChangedCallback);
	Binding::Manager::GetInstance().RegisterBoundDeviceContextReleaseHandler(DeviceContextReleaseHandler);
	BindingHandler::PrintBindingTable();
}

void BindingHandler::PrintBindingTable()
{
	Binding::Table &bindingTable = Binding::Table::GetInstance();

	LOG_INF("Binding Table size: [%d]:", bindingTable.Size());
	uint8_t i = 0;
	for (auto &entry : bindingTable) {
		switch (entry.type) {
		case Binding::MATTER_UNICAST_BINDING:
			LOG_INF("[%d] UNICAST:", i++);
			LOG_INF("\t\t+ Fabric: %d\n \
            \t+ LocalEndpoint %d \n \
            \t+ RemoteEndpointId %d \n \
            \t+ NodeId %d",
				(int)entry.fabricIndex, (int)entry.local, (int)entry.remote, (int)entry.nodeId);
			if (entry.clusterId.has_value()) {
				LOG_INF("\t\t+ ClusterId %d", (int)*entry.clusterId);
			} else {
				LOG_INF("\t\t+ ClusterId: none");
			}
			break;
		case Binding::MATTER_MULTICAST_BINDING:
			LOG_INF("[%d] GROUP:", i++);
			LOG_INF("\t\t+ Fabric: %d\n \
            \t+ LocalEndpoint %d \n \
            \t+ RemoteEndpointId %d \n \
            \t+ GroupId %d",
				(int)entry.fabricIndex, (int)entry.local, (int)entry.remote, (int)entry.groupId);
			break;
		case Binding::MATTER_UNUSED_BINDING:
			LOG_INF("[%d] UNUSED", i++);
			break;
		default:
			break;
		}
	}
}

void BindingHandler::DeviceWorkerHandler(intptr_t context)
{
	VerifyOrDie(context != 0);
	BindingData *data = reinterpret_cast<BindingData *>(context);

	if (Binding::Table::GetInstance().Size() != 0) {
		LOG_INF("Notify Bounded Cluster | endpoint: %d cluster: %d", data->EndpointId, data->ClusterId);
		CHIP_ERROR err = Binding::Manager::GetInstance().NotifyBoundClusterChanged(
			data->EndpointId, data->ClusterId, static_cast<void *>(data));
		if (CHIP_NO_ERROR != err) {
			LOG_ERR("NotifyBoundClusterChanged failed due to: %" CHIP_ERROR_FORMAT, err.Format());
		}
	} else {
		LOG_INF("NO DEVICE BOUND");
		Platform::Delete(data);
	}
}

} /* namespace Nrf::Matter */
