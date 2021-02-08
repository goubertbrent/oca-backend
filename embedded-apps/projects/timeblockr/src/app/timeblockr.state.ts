import { createFeatureSelector, createSelector } from '@ngrx/store';
import { CallStateType } from '@oca/shared';
import { TimeblockrClientDateSlot, TimeblockrDateSlot } from './timeblockr';
import { State, timeblockrFeatureKey } from './timeblockr.reducer';

const getTimeblockrState = createFeatureSelector<State>(timeblockrFeatureKey);


export const getAppointments = createSelector(getTimeblockrState, s => s.appointments.result);
export const isLoadingAppointments = createSelector(getTimeblockrState, s => s.appointments.state === CallStateType.LOADING);

export const getProducts = createSelector(getTimeblockrState, s => s.products.result ?? []);

export const getLocations = createSelector(getTimeblockrState, s => s.locations.result ?? []);

export const getDateSlots = createSelector(getTimeblockrState, s => (s.dateSlots.result ?? []).map(toClientDateSlot));

export const getTimeSLots = createSelector(getTimeblockrState, s => (s.timeslotsOnDay.result ?? []).map(toClientDateSlot));

export const getDynamicFields = createSelector(getTimeblockrState, s => s.dynamicFields.result ?? []);

export const isLoadingNewAppointmentData = createSelector(getTimeblockrState, s => [s.appointments, s.products, s.locations,
  s.dateSlots, s.timeslotsOnDay, s.dynamicFields].some(i => i.state === CallStateType.LOADING));

function toClientDateSlot(slot: TimeblockrDateSlot): TimeblockrClientDateSlot {
  return {
    date: new Date(slot.date),
    value: slot.date,
  };
}
