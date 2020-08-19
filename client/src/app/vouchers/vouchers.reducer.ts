import { initialStateResult, ResultState, stateError, stateLoading, stateSuccess } from '@oca/web-shared';
import { updateItem } from '../shared/util';
import { CirkloSettings, VouchersServiceList } from './vouchers';
import { VouchersActions, VouchersActionTypes } from './vouchers.actions';

export const vouchersFeatureKey = 'vouchers';

export interface VouchersState {
  services: ResultState<VouchersServiceList>;
  cirkloSettings: ResultState<CirkloSettings>;
}

export const initialState: VouchersState = {
  services: initialStateResult,
  cirkloSettings: initialStateResult,
};

export function vouchersReducer(state = initialState, action: VouchersActions): VouchersState {
  switch (action.type) {
    case VouchersActionTypes.GET_SERVICES:
      return { ...state, services: stateLoading(initialState.services.result) };
    case VouchersActionTypes.GET_SERVICES_SUCCESS:
      return {
        ...state,
        services: stateSuccess({ ...action.payload, results: [...(state.services.result?.results ?? []), ...action.payload.results] }),
      };
    case VouchersActionTypes.GET_SERVICES_FAILED:
      return { ...state, services: stateError(action.error, state.services.result) };
    case VouchersActionTypes.WHITELIST_VOUCHER_SERVICE:
      break;
    case VouchersActionTypes.WHITELIST_VOUCHER_SERVICE_SUCCESS:
      return {
        ...state,
        services: stateSuccess({
          ...(state.services.result as Readonly<VouchersServiceList>),
          results: updateItem((state.services.result as VouchersServiceList).results, action.payload.service, 'id'),
        }),
      };
    case VouchersActionTypes.WHITELIST_VOUCHER_SERVICE_FAILED:
      return { ...state, services: stateError(action.error, state.services.result) };
    case VouchersActionTypes.GET_CIRKLO_SETTINGS:
      return { ...state, cirkloSettings: stateLoading(initialState.cirkloSettings.result) };
    case VouchersActionTypes.GET_CIRKLO_SETTINGS_SUCCESS:
      return { ...state, cirkloSettings: stateSuccess(action.payload) };
    case VouchersActionTypes.GET_CIRKLO_SETTINGS_FAILED:
      return { ...state, cirkloSettings: stateError(action.error, state.cirkloSettings.result) };
    case VouchersActionTypes.SAVE_CIRKLO_SETTINGS:
      return { ...state, cirkloSettings: stateLoading(action.payload) };
    case VouchersActionTypes.SAVE_CIRKLO_SETTINGS_SUCCESS:
      return { ...state, cirkloSettings: stateSuccess(action.payload) };
    case VouchersActionTypes.SAVE_CIRKLO_SETTINGS_FAILED:
      return { ...state, cirkloSettings: stateError(action.error, state.cirkloSettings.result) };
  }
  return state;
}
