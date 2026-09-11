/*
 * Copyright (c) 2024 Nordic Semiconductor ASA
 *
 * SPDX-License-Identifier: LicenseRef-Nordic-5-Clause
 */

#pragma once

#include "app/task_executor.h"
#include "board/board.h"

#include <app/clusters/identify-server/IdentifyCluster.h>
#include <app/server-cluster/ServerClusterInterfaceRegistry.h>
#include <data-model-providers/codegen/CodegenDataModelProvider.h>
#include <lib/support/TimerDelegate.h>
#include <platform/DefaultTimerDelegate.h>

#include <functional>
#include <optional>

namespace Nrf
{
namespace Matter
{
	/**
	 * @brief Implementation of the Identify delegate for nRF development kits.
	 *
	 * This class is used to implement the Identify delegate for nRF development
	 * kits. It is used to blink the LED2 on an nRF development kit.
	 *
	 * This class is designed to be used as a base class for custom identify
	 * delegate implementations. Derived classes can override the virtual methods
	 * to customize the identify behavior.
	 *
	 * @note By default, trigger effects are disabled. Use the constructor
	 * parameter or SetTriggerEffectEnabled() to enable them.
	 */
	class IdentifyDelegateImplNrf : public chip::app::Clusters::IdentifyDelegate {
	public:
		/**
		 * @brief Construct a new IdentifyDelegateImplNrf object.
		 *
		 * @param isTriggerEffectEnabled Whether trigger effects are enabled.
		 *                               Defaults to false.
		 */
		explicit IdentifyDelegateImplNrf(bool isTriggerEffectEnabled = false,
						 std::function<void()> customIdentifyStopCallback = nullptr)
			: mIsTriggerEffectEnabled(isTriggerEffectEnabled),
			  mCustomIdentifyStopCallback(customIdentifyStopCallback)
		{
		}

		void OnIdentifyStart(chip::app::Clusters::IdentifyCluster &cluster) override
		{
			Nrf::PostTask([] {
				Nrf::GetBoard()
					.GetLED(Nrf::DeviceLeds::LED2)
					.Blink(Nrf::LedConsts::kIdentifyBlinkRate_ms);
			});
		}

		void OnIdentifyStop(chip::app::Clusters::IdentifyCluster &cluster) override
		{
			if (mCustomIdentifyStopCallback) {
				mCustomIdentifyStopCallback();
			} else {
				Nrf::PostTask([] { Nrf::GetBoard().GetLED(Nrf::DeviceLeds::LED2).Set(false); });
			}
		}

		void OnTriggerEffect(chip::app::Clusters::IdentifyCluster &cluster) override
		{
			switch (cluster.GetEffectIdentifier()) {
			case chip::app::Clusters::Identify::EffectIdentifierEnum::kBlink:
			case chip::app::Clusters::Identify::EffectIdentifierEnum::kBreathe:
				Nrf::PostTask([] {
					Nrf::GetBoard()
						.GetLED(Nrf::DeviceLeds::LED2)
						.Blink(Nrf::LedConsts::kTriggerEffectStart_ms,
						       Nrf::LedConsts::kTriggerEffectFinish_ms);
				});
				break;
			case chip::app::Clusters::Identify::EffectIdentifierEnum::kOkay:
			case chip::app::Clusters::Identify::EffectIdentifierEnum::kChannelChange:
				Nrf::PostTask([] { Nrf::GetBoard().GetLED(Nrf::DeviceLeds::LED2).Set(true); });
				break;
			case chip::app::Clusters::Identify::EffectIdentifierEnum::kFinishEffect:
			case chip::app::Clusters::Identify::EffectIdentifierEnum::kStopEffect:
				if (mCustomIdentifyStopCallback) {
					mCustomIdentifyStopCallback();
				} else {
					Nrf::PostTask([] { Nrf::GetBoard().GetLED(Nrf::DeviceLeds::LED2).Set(false); });
				}
				break;
			default:
				return;
			}
		}

		bool IsTriggerEffectEnabled() const override { return mIsTriggerEffectEnabled; }

	protected:
		bool mIsTriggerEffectEnabled = false;
		std::function<void()> mCustomIdentifyStopCallback;
	};

	/**
	 * @brief Identify Cluster implementation for nRF Connect SDK.
	 *
	 */
	class IdentifyCluster {
	public:
		IdentifyCluster(chip::EndpointId endpoint, chip::app::Clusters::IdentifyDelegate &identifyDelegate,
				chip::TimerDelegate &timerDelegate,
				chip::app::Clusters::Identify::IdentifyTypeEnum identifyType =
					chip::app::Clusters::Identify::IdentifyTypeEnum::kVisibleIndicator);

		explicit IdentifyCluster(chip::EndpointId endpoint, bool isTriggerEffectEnabled = false,
					 std::function<void()> customIdentifyStopCallback = nullptr,
					 chip::app::Clusters::Identify::IdentifyTypeEnum identifyType =
						 chip::app::Clusters::Identify::IdentifyTypeEnum::kVisibleIndicator);

		~IdentifyCluster();

	private:
		chip::EndpointId mEndpointId;
		std::optional<IdentifyDelegateImplNrf> mNrfDelegate;
		chip::app::Clusters::IdentifyDelegate * mDelegate = nullptr;
		chip::app::DefaultTimerDelegate mDefaultTimerDelegate;
		chip::app::RegisteredServerCluster<chip::app::Clusters::IdentifyCluster> mIdentifyCluster;
	};

} // namespace Matter
} // namespace Nrf
