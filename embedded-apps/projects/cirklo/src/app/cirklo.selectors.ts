import { createFeatureSelector, createSelector } from '@ngrx/store';
import { getServiceData } from '@oca/rogerthat';
import { CallStateType } from '@oca/shared';
import { CirkloInfo, CirkloMerchant, CirkloVouchersList } from './cirklo';
import { cirkloFeatureKey, CirkloState } from './cirklo.reducer';

export const selectCirkloState = createFeatureSelector<CirkloState>(cirkloFeatureKey);

export const getVouchersList = createSelector(selectCirkloState, s => s.vouchers.result);
export const isVoucherListLoading = createSelector(selectCirkloState, s => s.vouchers.state === CallStateType.LOADING);

export const getVoucher = createSelector(getVouchersList, (s: CirkloVouchersList | null, voucherId: string) => {
  return s?.results.find(r => r.id === voucherId);
});

export const getVoucherTransactions = createSelector(selectCirkloState, s => s.transactions.result?.results ?? []);
export const areTransactionsLoading = createSelector(selectCirkloState, s => s.transactions.state === CallStateType.LOADING);

export const getMerchants = createSelector(selectCirkloState, s => s.merchants.result?.results ?? []);
export const getMerchantsCursor = createSelector(selectCirkloState, s => s.merchants.result?.cursor);
export const areMerchantsLoading = createSelector(selectCirkloState, s => s.merchants.state === CallStateType.LOADING);
export const hasMoreMerchants = createSelector(selectCirkloState, s => s.merchants.result?.more ?? true);
export const getMerchant = createSelector(getMerchants, (s: CirkloMerchant[], merchantId: string) => s.find(m => m.id === merchantId));


interface ServiceData {
  cirkloInfo?: CirkloInfo;
}

export const getCirkloInfo = createSelector(getServiceData, (s: ServiceData) => s.cirkloInfo);
