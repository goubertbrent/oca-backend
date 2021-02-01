import { createFeatureSelector, createSelector } from '@ngrx/store';
import { CallStateType, initialStateResult, ResultState } from '@oca/shared';
import { Appointment, ListAppointments, ListBranches, ListDates, ListServices, ListTimes, QmaticClientSettings } from './appointments';

export const Q_MATIC_FEATURE = 'qmatic';

export interface QMaticState {
  appointments: ResultState<ListAppointments>;
  services: ResultState<ListServices>;
  branches: ResultState<ListBranches>;
  dates: ResultState<ListDates>;
  times: ResultState<ListTimes>;
  reservedAppointment: ResultState<Appointment>;
  settings: ResultState<QmaticClientSettings>;
}

const getQMaticState = createFeatureSelector<QMaticState>(Q_MATIC_FEATURE);

export const initialQMaticState: QMaticState = {
  appointments: initialStateResult,
  services: initialStateResult,
  branches: initialStateResult,
  dates: initialStateResult,
  times: initialStateResult,
  reservedAppointment: initialStateResult,
  settings: initialStateResult,
};

export const getAppointments = createSelector(getQMaticState, s => s.appointments);
export const getAppointmentsList = createSelector(getQMaticState, s => {
  const items = s.appointments.state === CallStateType.SUCCESS ? s.appointments.result.appointmentList : [];
  const now = new Date();
  const results = items.map(item => ({ ...item, start: new Date(item.start), end: new Date(item.end) }))
    .sort((first, second) => {
      return first.start.getTime() < second.start.getTime() ? -1 : 1;
    });
  return {
    upcoming: results.filter(r => r.start > now),
    past: results.filter(r => r.start <= now),
  };
});

export const getServices = createSelector(getQMaticState, s => s.services.state === CallStateType.SUCCESS
  ? s.services.result.serviceList :
  []);
export const getBranches = createSelector(getQMaticState, s => s.branches.state === CallStateType.SUCCESS ?
  s.branches.result.branchList
  : []);
export const getDates = createSelector(getQMaticState, s => s.dates.state === CallStateType.SUCCESS ?
  s.dates.result.dates.map(d => new Date(d))
  : []);
export const getTimes = createSelector(getQMaticState, s => s.times.state === CallStateType.SUCCESS ?
  s.times.result.times :
  []);
export const getReservedAppointment = createSelector(getQMaticState, s => s.reservedAppointment);
export const isLoadingNewAppointmentInfo = createSelector(getQMaticState, s =>
  [s.services, s.branches, s.dates, s.times, s.reservedAppointment].some(status => status.state === CallStateType.LOADING));
export const getClientSettings = createSelector(getQMaticState, s => s.settings.result);
