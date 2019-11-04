import { CallStateType, stateError, stateLoading, stateSuccess } from '../shared/call-state';
import { QMaticActions, QMaticActionTypes } from './q-matic-actions';
import { initialQMaticState, QMaticState } from './q-matic.state';

export function qmaticReducer(state = initialQMaticState, action: QMaticActions): QMaticState {
  switch (action.type) {
    case QMaticActionTypes.GET_APPOINTMENTS:
      return { ...state, appointments: stateLoading(initialQMaticState.appointments.result) };
    case QMaticActionTypes.GET_APPOINTMENTS_SUCCESS:
      return { ...state, appointments: stateSuccess(action.payload) };
    case QMaticActionTypes.GET_APPOINTMENTS_FAILED:
      return { ...state, appointments: stateError(action.error, state.appointments.result) };
    case QMaticActionTypes.GET_SERVICES:
      return { ...state, services: stateLoading(initialQMaticState.services.result) };
    case QMaticActionTypes.GET_SERVICES_SUCCESS:
      return { ...state, services: stateSuccess(action.payload) };
    case QMaticActionTypes.GET_SERVICES_FAILED:
      return { ...state, services: stateError(action.error, state.services.result) };
    case QMaticActionTypes.GET_BRANCHES:
      return { ...state, branches: stateLoading(initialQMaticState.branches.result) };
    case QMaticActionTypes.GET_BRANCHES_SUCCESS:
      return { ...state, branches: stateSuccess(action.payload) };
    case QMaticActionTypes.GET_BRANCHES_FAILED:
      return { ...state, branches: stateError(action.error, state.branches.result) };
    case QMaticActionTypes.GET_DATES:
      return { ...state, dates: stateLoading(initialQMaticState.dates.result) };
    case QMaticActionTypes.GET_DATES_SUCCESS:
      return { ...state, dates: stateSuccess(action.payload) };
    case QMaticActionTypes.GET_DATES_FAILED:
      return { ...state, dates: stateError(action.error, state.dates.result) };
    case QMaticActionTypes.GET_TIMES:
      return { ...state, times: stateLoading(initialQMaticState.times.result) };
    case QMaticActionTypes.GET_TIMES_SUCCESS:
      return { ...state, times: stateSuccess(action.payload) };
    case QMaticActionTypes.GET_TIMES_FAILED:
      return { ...state, times: stateError(action.error, state.times.result) };
    case QMaticActionTypes.RESERVE_DATE:
      return { ...state, reservedAppointment: stateLoading(initialQMaticState.reservedAppointment.result) };
    case QMaticActionTypes.RESERVE_DATE_SUCCESS:
      return { ...state, reservedAppointment: stateSuccess(action.payload) };
    case QMaticActionTypes.RESERVE_DATE_FAILED:
      return { ...state, reservedAppointment: stateError(action.error, state.reservedAppointment.result) };
    case QMaticActionTypes.CONFIRM_APPOINTMENT_SUCCESS:
      if (state.appointments.state === CallStateType.SUCCESS) {
        return {
          ...state,
          appointments: stateSuccess({
            ...state.appointments.result,
            appointmentList: [...state.appointments.result.appointmentList, action.payload],
          }),
        };
      }
      break;
    case QMaticActionTypes.CANCEL_APPOINTMENT_SUCCESS:
      if (state.appointments.state === CallStateType.SUCCESS) {
        return {
          ...state, appointments: stateSuccess({
            ...state.appointments.result,
            appointmentList: state.appointments.result.appointmentList.filter(a => a.publicId !== action.payload.appointment_id),
          }),
        };
      }
      break;
  }
  return state;
}
