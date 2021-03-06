import { createFeatureSelector, createSelector } from '@ngrx/store';
import { CallStateType } from '@oca/web-shared';
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
export const voucherServicesLoading = createSelector(featureState, s => s.services.state === CallStateType.LOADING);
export const areCirkloSettingsLoading = createSelector(featureState, s => s.cirkloSettings.state === CallStateType.LOADING);
export const getCirkloSettings = createSelector(featureState, s => s.cirkloSettings.result);
export const getCirkloCities = createSelector(featureState, s => s.cirkloCities.result ?? []);
export const isExporting = createSelector(featureState, s => s.merchantsExport.state === CallStateType.LOADING);
