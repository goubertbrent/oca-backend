import { createFeatureSelector, createSelector } from '@ngrx/store';
import { CallStateType } from '../shared/util';
import { VouchersServiceList } from './vouchers';
import { vouchersFeatureKey, VouchersState } from './vouchers.reducer';

export const featureState = createFeatureSelector<VouchersState>(vouchersFeatureKey);

export const getVoucherList = createSelector(featureState, (s): VouchersServiceList => s.services.result || {
  results: [],
  cursor: null,
  total: 0,
  more: false,
});
export const getVoucherServices = createSelector(getVoucherList, s => s.results);
export const voucherServicesLoading = createSelector(featureState, s => s.services.state === CallStateType.LOADING
  || s.export.state === CallStateType.LOADING);
