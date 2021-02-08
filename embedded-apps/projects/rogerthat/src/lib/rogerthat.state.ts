import { createFeatureSelector, createSelector } from '@ngrx/store';
import { GetNewsStreamItemsResponseTO, NewsSenderTO, QrCodeScannedContent } from 'rogerthat-plugin';
import { CallStateType, initialStateResult, ResultState } from '@oca/shared';
import { ServiceData, UserData } from './rogerthat';

export interface RogerthatState<UserDataType = UserData, ServiceDataType = ServiceData> {
  userData: UserDataType;
  serviceData: ServiceDataType;
  scannedQrCode: ResultState<QrCodeScannedContent>;
  newsStreamItems: ResultState<GetNewsStreamItemsResponseTO>;
}

const getRogerthatState = createFeatureSelector<RogerthatState>('rogerthat');

export const initialRogerthatState: RogerthatState<UserData, ServiceData> = {
  userData: {},
  serviceData: {},
  scannedQrCode: initialStateResult,
  newsStreamItems: initialStateResult,
};

export const getScannedQr = createSelector(getRogerthatState, s => s.scannedQrCode);

export const getUserData = createSelector(getRogerthatState, s => s.userData);
export const getServiceData = createSelector(getRogerthatState, s => s.serviceData);
export const getNewsStreamItems = createSelector(getRogerthatState, s => s.newsStreamItems);
export const shouldShowNews = createSelector(getRogerthatState, s => s.newsStreamItems.state !== CallStateType.SUCCESS
  || s.newsStreamItems.state === CallStateType.SUCCESS && s.newsStreamItems.result.items.length > 0);
export const isNewsStreamItemsLoading = createSelector(getNewsStreamItems, s => s.state === CallStateType.LOADING);
export const getNewsStreamItemsList = createSelector(getNewsStreamItems, s => {
  const items = s.state === CallStateType.SUCCESS ? s.result.items : [];
  return items.map(item => ({
    ...item,
    date: new Date(item.timestamp * 1000),
    sender: {
      ...(item.sender as NewsSenderTO),
      avatar_url: `${rogerthat.system.baseUrl}/unauthenticated/mobi/cached/avatar/${(item.sender as NewsSenderTO).avatar_id}`,
    },
  }));
});


