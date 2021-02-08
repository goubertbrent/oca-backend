import { ActionReducerMap, createReducer, on } from '@ngrx/store';
import { rogerthatReducer, RogerthatState } from '@oca/rogerthat';
import { initialStateResult, ResultState, stateError, stateLoading, stateSuccess } from '@oca/shared';
import { TimeblockrAppointment, TimeblockrDateSlot, TimeblockrDynamicField, TimeblockrLocation, TimeblockrProduct } from './timeblockr';
import {
  loadAppointments,
  loadAppointmentsFailure,
  loadAppointmentsSuccess,
  loadDynamicFields,
  loadDynamicFieldsFailure,
  loadDynamicFieldsSuccess,
  loadLocations,
  loadLocationsFailure,
  loadLocationsSuccess,
  loadProducts,
  loadProductsFailure,
  loadProductsSuccess,
  loadTimeslots,
  loadTimeslotsFailure,
  loadTimeslotsOnDay,
  loadTimeslotsOnDayFailure,
  loadTimeslotsOnDaySuccess,
  loadTimeslotsSuccess,
} from './timeblockr.actions';

export const timeblockrFeatureKey = 'timeblockr';

export interface State {
  appointments: ResultState<TimeblockrAppointment[]>;
  products: ResultState<TimeblockrProduct[]>;
  locations: ResultState<TimeblockrLocation[]>;
  dateSlots: ResultState<TimeblockrDateSlot[]>;
  timeslotsOnDay: ResultState<TimeblockrDateSlot[]>;
  dynamicFields: ResultState<TimeblockrDynamicField[]>;
}

export const initialState: State = {
  appointments: initialStateResult,
  products: initialStateResult,
  locations: initialStateResult,
  dateSlots: initialStateResult,
  timeslotsOnDay: initialStateResult,
  dynamicFields: initialStateResult,
};

export interface TimeblockrAppState {
  rogerthat: RogerthatState;
  [ timeblockrFeatureKey ]: State;
}

export const timeblockrReducer = createReducer(
  initialState,
  on(loadAppointments, (state) => ({ ...state, appointments: stateLoading(initialState.appointments.result) })),
  on(loadAppointmentsSuccess, (state, { data }) => ({ ...state, appointments: stateSuccess(data) })),
  on(loadAppointmentsFailure, (state, { error }) => ({ ...state, appointments: stateError(error, state.appointments.result) })),
  on(loadProducts, (state) => ({
    ...state,
    products: stateLoading(initialState.products.result),
    dateSlots: initialState.dateSlots,
    timeslotsOnDay: initialState.timeslotsOnDay,
    dynamicFields: initialState.dynamicFields,
  })),
  on(loadProductsSuccess, (state, { data }) => ({ ...state, products: stateSuccess(data) })),
  on(loadProductsFailure, (state, { error }) => ({ ...state, products: stateError(error, state.products.result) })),
  on(loadLocations, (state) => ({ ...state, locations: stateLoading(initialState.locations.result) })),
  on(loadLocationsSuccess, (state, { data }) => ({ ...state, locations: stateSuccess(data) })),
  on(loadLocationsFailure, (state, { error }) => ({ ...state, locations: stateError(error, state.locations.result) })),
  on(loadTimeslots, (state) => ({
    ...state,
    dateSlots: stateLoading(initialState.dateSlots.result),
    timeslotsOnDay: initialState.timeslotsOnDay,
  })),
  on(loadTimeslotsSuccess, (state, { data }) => ({ ...state, dateSlots: stateSuccess(data) })),
  on(loadTimeslotsFailure, (state, { error }) => ({ ...state, dateSlots: stateError(error, state.dateSlots.result) })),
  on(loadTimeslotsOnDay, (state) => ({ ...state, timeslotsOnDay: stateLoading(initialState.timeslotsOnDay.result) })),
  on(loadTimeslotsOnDaySuccess, (state, { data }) => ({ ...state, timeslotsOnDay: stateSuccess(data) })),
  on(loadTimeslotsOnDayFailure, (state, { error }) => ({ ...state, timeslotsOnDay: stateError(error, state.timeslotsOnDay.result) })),
  on(loadDynamicFields, (state) => ({ ...state, dynamicFields: stateLoading(initialState.dynamicFields.result) })),
  on(loadDynamicFieldsSuccess, (state, { data }) => ({ ...state, dynamicFields: stateSuccess(data) })),
  on(loadDynamicFieldsFailure, (state, { error }) => ({ ...state, dynamicFields: stateError(error, state.dynamicFields.result) })),
);

export const timeblockrAppReducers: ActionReducerMap<TimeblockrAppState> = {
  rogerthat: rogerthatReducer,
  [ timeblockrFeatureKey ]: timeblockrReducer,
} as any;
