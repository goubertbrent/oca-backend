import { initialStateResult, stateError, stateLoading, stateSuccess } from '@oca/shared';
import { TrashState } from './state';
import { TrashActions, TrashActionTypes } from './trash.actions';

export const initialTrashState: TrashState = {
  streets: initialStateResult,
  houseNumbers: initialStateResult,
  setAddress: initialStateResult,
  setNotifications: initialStateResult,
};

export function trashReducer(state = initialTrashState, action: TrashActions): TrashState {
  switch (action.type) {
    case TrashActionTypes.GetStreets:
      return { ...state, streets: stateLoading(initialTrashState.streets.result) };
    case TrashActionTypes.GetStreetsSuccess:
      return { ...state, streets: stateSuccess(action.payload) };
    case TrashActionTypes.GetStreetsFailure:
      return { ...state, streets: stateError(action.error, state.streets.result) };
    case TrashActionTypes.GetHouseNumbers:
      return { ...state, houseNumbers: stateLoading(initialTrashState.houseNumbers.result) };
    case TrashActionTypes.GetHouseNumbersSuccess:
      return { ...state, houseNumbers: stateSuccess(action.payload) };
    case TrashActionTypes.GetHouseNumbersFailure:
      return { ...state, houseNumbers: stateError(action.error, state.houseNumbers.result) };
    case TrashActionTypes.SaveAddress:
      return { ...state, setAddress: stateLoading(initialTrashState.setAddress.result) };
    case TrashActionTypes.SaveAddressSuccess:
      return { ...state, setAddress: stateSuccess(null) };
    case TrashActionTypes.SaveAddressFailure:
      return { ...state, setAddress: stateError(action.error, state.setAddress.result) };
    case TrashActionTypes.SaveNotifications:
      return { ...state, setNotifications: stateLoading(initialTrashState.setNotifications.result) };
    case TrashActionTypes.SaveNotificationsSuccess:
      return { ...state, setNotifications: stateSuccess(null) };
    case TrashActionTypes.SaveNotificationsFailure:
      return { ...state, setNotifications: stateError(action.error, state.setNotifications.result) };
  }
  return state;
}
