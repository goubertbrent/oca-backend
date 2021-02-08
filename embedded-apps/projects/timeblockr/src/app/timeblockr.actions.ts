import { createAction, props } from '@ngrx/store';
import {
  CreateTimeblockrAppointment,
  SelectedProduct,
  TimeblockrAppointment,
  TimeblockrDateSlot,
  TimeblockrDynamicField,
  TimeblockrLocation,
  TimeblockrProduct,
} from './timeblockr';

export const loadAppointments = createAction(
  '[Timeblockr] Load Appointments',
);

export const loadAppointmentsSuccess = createAction(
  '[Timeblockr] Load Appointments Success',
  props<{ data: TimeblockrAppointment[] }>(),
);

export const loadAppointmentsFailure = createAction(
  '[Timeblockr] Load Appointments Failure',
  props<{ error: string }>(),
);

export const loadProducts = createAction(
  '[Timeblockr] Load Products',
  props<{ data: { selectedProducts: SelectedProduct[] } }>(),
);

export const loadProductsSuccess = createAction(
  '[Timeblockr] Load Products Success',
  props<{ data: TimeblockrProduct[] }>(),
);

export const loadProductsFailure = createAction(
  '[Timeblockr] Load Products Failure',
  props<{ error: string }>(),
);

export const loadLocations = createAction(
  '[Timeblockr] Load Locations',
);

export const loadLocationsSuccess = createAction(
  '[Timeblockr] Load Locations Success',
  props<{ data: TimeblockrLocation[] }>(),
);

export const loadLocationsFailure = createAction(
  '[Timeblockr] Load Locations Failure',
  props<{ error: string }>(),
);

export const loadTimeslots = createAction(
  '[Timeblockr] Load Timeslots',
  props<{ data: { selectedProducts: SelectedProduct[]; locationId: string; } }>(),
);

export const loadTimeslotsSuccess = createAction(
  '[Timeblockr] Load Timeslots Success',
  props<{ data: TimeblockrDateSlot[] }>(),
);

export const loadTimeslotsFailure = createAction(
  '[Timeblockr] Load Timeslots Failure',
  props<{ error: string }>(),
);

export const loadTimeslotsOnDay = createAction(
  '[Timeblockr] Load TimeslotsOnDay',
  props<{ data: { selectedProducts: SelectedProduct[]; locationId: string; selectedDate: string; } }>(),
);

export const loadTimeslotsOnDaySuccess = createAction(
  '[Timeblockr] Load TimeslotsOnDay Success',
  props<{ data: TimeblockrDateSlot[] }>(),
);

export const loadTimeslotsOnDayFailure = createAction(
  '[Timeblockr] Load TimeslotsOnDay Failure',
  props<{ error: string }>(),
);

export const loadDynamicFields = createAction(
  '[Timeblockr] Load DynamicFields',
  props<{ data: { selectedProducts: SelectedProduct[]; locationId: string; } }>(),
);

export const loadDynamicFieldsSuccess = createAction(
  '[Timeblockr] Load DynamicFields Success',
  props<{ data: TimeblockrDynamicField[] }>(),
);

export const loadDynamicFieldsFailure = createAction(
  '[Timeblockr] Load DynamicFields Failure',
  props<{ error: string }>(),
);

export const createAppointment = createAction(
  '[Timeblockr] Create appointment',
  props<{ data: CreateTimeblockrAppointment }>(),
);

export const createAppointmentSuccess = createAction(
  '[Timeblockr] Create appointment Success',
  props<{ data: TimeblockrAppointment }>(),
);

export const createAppointmentFailure = createAction(
  '[Timeblockr] Create appointment Failure',
  props<{ error: string }>(),
);
