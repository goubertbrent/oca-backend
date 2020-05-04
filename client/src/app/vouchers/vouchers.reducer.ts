import { initialStateResult, patchItem, ResultState, stateError, stateLoading, stateSuccess, updateItem } from '../shared/util';
import { ExportVoucherServices, VouchersServiceList } from './vouchers';
import { VouchersActions, VouchersActionTypes } from './vouchers.actions';

export const vouchersFeatureKey = 'vouchers';

export interface VouchersState {
  services: ResultState<VouchersServiceList>;
  export: ResultState<ExportVoucherServices>;
}

export const initialState: VouchersState = {
  services: initialStateResult,
  export: initialStateResult,
};

export function vouchersReducer(state = initialState, action: VouchersActions): VouchersState {
  switch (action.type) {
    case VouchersActionTypes.GET_SERVICES:
      return { ...state, services: stateLoading(action.payload.cursor ? state.services.result : initialState.services.result) };
    case VouchersActionTypes.GET_SERVICES_SUCCESS:
      return {
        ...state,
        services: stateSuccess({ ...action.payload, results: [...(state.services.result?.results ?? []), ...action.payload.results] }),
      };
    case VouchersActionTypes.GET_SERVICES_FAILED:
      return { ...state, services: stateError(action.payload.error, state.services.result) };
    case VouchersActionTypes.SAVE_VOUCHER_PROVIDER:
      break;
    case VouchersActionTypes.SAVE_VOUCHER_SETTINGS_SUCCESS:
      return {
        ...state,
        services: stateSuccess({
          ...(state.services.result as Readonly<VouchersServiceList>),
          results: updateItem((state.services.result as VouchersServiceList).results, action.payload.service, 'service_email'),
        }),
      };
    case VouchersActionTypes.SAVE_VOUCHER_FAILED:
      return { ...state, services: stateError(action.payload.error, state.services.result) };
    case VouchersActionTypes.EXPORT_VOUCHER_SERVICES:
      return { ...state, export: stateLoading(initialState.export.result) };
    case VouchersActionTypes.EXPORT_VOUCHER_SERVICES_SUCCESS:
      return { ...state, export: stateSuccess(action.payload) };
    case VouchersActionTypes.EXPORT_VOUCHER_SERVICES_FAILED:
      return { ...state, export: stateError(action.payload.error, state.export.result) };
  }
  return state;
}
