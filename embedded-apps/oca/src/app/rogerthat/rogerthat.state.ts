import { createFeatureSelector, createSelector } from '@ngrx/store';
import { QrCodeScannedContent } from 'rogerthat-plugin';
import { initialStateResult, ResultState } from '../shared/call-state';
import { ServiceData, UserData } from './rogerthat';

export interface RogerthatState<UserDataType = any, ServiceDataType = any> {
  userData: UserDataType;
  serviceData: ServiceDataType;
  scannedQrCode: ResultState<QrCodeScannedContent>;
}

const getRogerthatState = createFeatureSelector<RogerthatState>('rogerthat');

export const initialRogerthatState: RogerthatState<UserData, ServiceData> = {
  userData: {},
  serviceData: {},
  scannedQrCode: initialStateResult,
};

export const getScannedQr = createSelector(getRogerthatState, s => s.scannedQrCode);

export const getUserData = createSelector(getRogerthatState, s => s.userData);
export const getServiceData = createSelector(getRogerthatState, s => s.serviceData);


