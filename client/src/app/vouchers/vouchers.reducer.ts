import { createReducer, on } from '@ngrx/store';
import { initialStateResult, ResultState, stateError, stateLoading, stateSuccess } from '@oca/web-shared';
import { updateItem } from '../shared/util';
import { CirkloCity, CirkloSettings, VouchersServiceList } from './vouchers';
import {
  ExportMerchants,
  ExportMerchantsComplete,
  ExportMerchantsFailed,
  GetCirkloCities,
  GetCirkloCitiesComplete,
  GetCirkloCitiesFailed,
  GetCirkloSettingsAction,
  GetCirkloSettingsCompleteAction,
  GetCirkloSettingsFailedAction,
  GetServicesAction,
  GetServicesFailedAction,
  GetServicesSuccessAction,
  SaveCirkloSettingsAction,
  SaveCirkloSettingsCompleteAction,
  SaveCirkloSettingsFailedAction,
  WhitelistVoucherServiceFailedAction,
  WhitelistVoucherServiceSuccessAction,
} from './vouchers.actions';

export const vouchersFeatureKey = 'vouchers';

export interface VouchersState {
  services: ResultState<VouchersServiceList>;
  cirkloSettings: ResultState<CirkloSettings>;
  cirkloCities: ResultState<CirkloCity[]>;
  merchantsExport: ResultState<string>;
}

export const initialState: VouchersState = {
  services: initialStateResult,
  cirkloSettings: initialStateResult,
  cirkloCities: initialStateResult,
  merchantsExport: initialStateResult,
};

export const vouchersReducer = createReducer(
  initialState,
  on(GetServicesAction, (state) => ({ ...state, services: stateLoading(initialState.services.result) })),
  on(GetServicesSuccessAction, (state, { payload }) => ({
    ...state,
    services: stateSuccess({ ...payload, results: [...(state.services.result?.results ?? []), ...payload.results] }),
  })),
  on(GetServicesFailedAction, (state, { error }) => ({ ...state, services: stateError(error, state.services.result) })),
  on(WhitelistVoucherServiceSuccessAction, (state, { service }) => ({
    ...state,
    services: stateSuccess({
      ...(state.services.result as Readonly<VouchersServiceList>),
      results: updateItem((state.services.result as VouchersServiceList).results, service, 'id'),
    }),
  })),
  on(WhitelistVoucherServiceFailedAction, (state, { error }) => ({ ...state, services: stateError(error, state.services.result) })),
  on(GetCirkloSettingsAction, (state) => ({ ...state, cirkloSettings: stateLoading(initialState.cirkloSettings.result) })),
  on(GetCirkloSettingsCompleteAction, (state, { payload }) => ({ ...state, cirkloSettings: stateSuccess(payload) })),
  on(GetCirkloSettingsFailedAction, (state, { error }) => ({ ...state, cirkloSettings: stateError(error, state.cirkloSettings.result) })),
  on(SaveCirkloSettingsAction, (state, { payload }) => ({ ...state, cirkloSettings: stateLoading(payload) })),
  on(SaveCirkloSettingsCompleteAction, (state, { payload }) => ({ ...state, cirkloSettings: stateSuccess(payload) })),
  on(SaveCirkloSettingsFailedAction, (state, { error }) => ({ ...state, cirkloSettings: stateError(error, state.cirkloSettings.result) })),
  on(GetCirkloCities, (state) => ({ ...state, cirkloCities: stateLoading(state.cirkloCities.result) })),
  on(GetCirkloCitiesComplete, (state, { cities }) => ({ ...state, cirkloCities: stateSuccess(cities) })),
  on(GetCirkloCitiesFailed, (state, { error }) => ({ ...state, cirkloCities: stateError(error, state.cirkloCities.result) })),
  on(ExportMerchants, (state) => ({ ...state, merchantsExport: stateLoading(state.merchantsExport.result) })),
  on(ExportMerchantsComplete, (state, { url }) => ({ ...state, merchantsExport: stateSuccess(url) })),
  on(ExportMerchantsFailed, (state, { error }) => ({ ...state, merchantsExport: stateError(error, state.merchantsExport.result) })),
);
