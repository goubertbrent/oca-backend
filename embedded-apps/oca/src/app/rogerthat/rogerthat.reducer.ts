import { stateError, stateLoading, stateSuccess } from '../shared/call-state';
import { ServiceData, UserData } from './rogerthat';
import { RogerthatActions, RogerthatActionTypes } from './rogerthat.actions';
import { initialRogerthatState, RogerthatState } from './rogerthat.state';

export function rogerthatReducer(state = initialRogerthatState, action: RogerthatActions): RogerthatState<UserData, ServiceData> {
  switch (action.type) {
    case RogerthatActionTypes.SET_USER_DATA:
      return { ...state, userData: action.payload };
    case RogerthatActionTypes.SET_SERVICE_DATA:
      return { ...state, serviceData: action.payload };
    case RogerthatActionTypes.SCAN_QR_CODE:
      return { ...state, scannedQrCode: stateLoading(initialRogerthatState.scannedQrCode.result) };
    case RogerthatActionTypes.SCAN_QR_CODE_UPDATE:
      return { ...state, scannedQrCode: stateSuccess(action.payload) };
    case RogerthatActionTypes.SCAN_QR_CODE_FAILED:
      return { ...state, scannedQrCode: stateError(action.error, initialRogerthatState.scannedQrCode.result) };
    case RogerthatActionTypes.GET_NEWS_STREAM_ITEMS:
      return { ...state, newsStreamItems: stateLoading(initialRogerthatState.newsStreamItems.result) };
    case RogerthatActionTypes.GET_NEWS_STREAM_ITEMS_COMPLETE:
      return { ...state, newsStreamItems: stateSuccess(action.payload) };
    case RogerthatActionTypes.GET_NEWS_STREAM_ITEMS_FAILED:
      return { ...state, newsStreamItems: stateError(action.error, initialRogerthatState.newsStreamItems.result) };
  }
  return state;
}
