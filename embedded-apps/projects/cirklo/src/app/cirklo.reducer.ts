import { ActionReducerMap } from '@ngrx/store';
import { rogerthatReducer, RogerthatState } from '@oca/rogerthat';
import { initialStateResult, ResultState, stateError, stateLoading, stateSuccess } from '@oca/shared';
import { CirkloMerchantsList, CirkloVouchersList, VoucherTransactionsList } from './cirklo';
import { CirkloActions, CirkloActionTypes } from './cirklo.actions';

export const cirkloFeatureKey = 'cirklo';

export interface CirkloAppState {
  rogerthat: RogerthatState;
  [cirkloFeatureKey]: CirkloState;
}

export const cirkloAppReducers: ActionReducerMap<CirkloAppState> = {
  rogerthat: rogerthatReducer,
  [cirkloFeatureKey]: cirkloReducer,
} as any;

export interface CirkloState {
  vouchers: ResultState<CirkloVouchersList>;
  transactions: ResultState<VoucherTransactionsList>;
  merchants: ResultState<CirkloMerchantsList>;
}

export const initialState: CirkloState = {
  vouchers: initialStateResult,
  transactions: initialStateResult,
  merchants: initialStateResult,
};

export function cirkloReducer(state: CirkloState = initialState, action: CirkloActions): CirkloState {
  switch (action.type) {
    case CirkloActionTypes.CONFIRM_DELETE_VOUCHER:
    case CirkloActionTypes.CONFIRM_DELETE_VOUCHER_CANCELLED:
      break;
    case CirkloActionTypes.GET_VOUCHERS:
      return { ...state, vouchers: stateLoading(state.vouchers.result) };
    case CirkloActionTypes.GET_VOUCHERS_SUCCESS:
      return { ...state, vouchers: stateSuccess(action.payload) };
    case CirkloActionTypes.GET_VOUCHERS_FAILED:
      return { ...state, vouchers: stateError(action.error, state.vouchers.result) };
    case CirkloActionTypes.DELETE_VOUCHER:
      return { ...state, vouchers: stateLoading(state.vouchers.result) };
    case CirkloActionTypes.DELETE_VOUCHER_SUCCESS:
      return {
        ...state,
        vouchers: state.vouchers.result ? stateSuccess({
          ...state.vouchers.result,
          results: state.vouchers.result.results.filter(r => r.id !== action.payload.id),
        }) : initialState.vouchers,
      };
    case CirkloActionTypes.DELETE_VOUCHER_FAILED:
      return { ...state, vouchers: stateError(action.error, state.vouchers.result) };
    case CirkloActionTypes.GET_VOUCHER_TRANSACTIONS:
      return { ...state, transactions: stateLoading(initialState.transactions.result) };
    case CirkloActionTypes.GET_VOUCHER_TRANSACTIONS_SUCCESS:
      return { ...state, transactions: stateSuccess(action.payload) };
    case CirkloActionTypes.GET_VOUCHER_TRANSACTIONS_FAILED:
      return { ...state, transactions: stateError(action.error, state.transactions.result) };
    case CirkloActionTypes.ADD_VOUCHER:
      return { ...state, vouchers: stateLoading(state.vouchers.result) };
    case CirkloActionTypes.ADD_VOUCHER_SUCCESS:
      return {
        ...state,
        vouchers: state.vouchers.result ? stateSuccess({
          ...state.vouchers.result,
          cities: {...state.vouchers.result.cities, [action.payload.city.city_id]: {logo_url: action.payload.city.logo_url}},
          results: [...state.vouchers.result.results, action.payload.voucher],
        }) : initialState.vouchers,
      };
    case CirkloActionTypes.ADD_VOUCHER_FAILED:
      return { ...state, vouchers: stateError(action.error, state.vouchers.result) };
    case CirkloActionTypes.GET_MERCHANTS:
      return { ...state, merchants: stateLoading(state.merchants.result) };
    case CirkloActionTypes.GET_MERCHANTS_SUCCESS:
      return {
        ...state,
        merchants: stateSuccess(state.merchants.result ? {
          ...action.payload,
          results: [...state.merchants.result.results, ...action.payload.results],
        } : action.payload),
      };
    case CirkloActionTypes.GET_MERCHANTS_FAILED:
      return { ...state, merchants: stateError(action.error, state.merchants.result) };
  }
  return state;
}
