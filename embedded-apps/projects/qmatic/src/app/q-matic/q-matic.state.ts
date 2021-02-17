import { createFeatureSelector, createSelector } from '@ngrx/store';
import { CallStateType, initialStateResult, ResultState } from '@oca/shared';
import {
  Appointment,
  ListAppointments,
  ListBranches,
  ListDates,
  ListServices,
  ListTimes,
  QmaticClientSettings,
  QMaticParsedService,
  QMaticService,
} from './appointments';

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

export const getAppointmentsState = createSelector(getQMaticState, s => s.appointments);
export const getAppointmentsList = createSelector(getAppointmentsState, s => {
  const items = s.state === CallStateType.SUCCESS ? s.result.appointmentList : [];
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

export const getServicesState = createSelector(getQMaticState, s => s.services);
export const getServices = createSelector(getServicesState, s => s.state === CallStateType.SUCCESS ?
  s.result.serviceList.map(service => parseService(service))
  : []);
export const getBranchesState = createSelector(getQMaticState, s => s.branches);
export const getBranches = createSelector(getBranchesState, s => s.state === CallStateType.SUCCESS ? s.result.branchList : []);
export const getDatesState = createSelector(getQMaticState, s => s.dates);
export const getDates = createSelector(getDatesState, s => s.state === CallStateType.SUCCESS ?
  s.result.dates.map(d => new Date(d))
  : []);
export const getTimesState = createSelector(getQMaticState, s => s.times);
export const getTimes = createSelector(getTimesState, s => s.state === CallStateType.SUCCESS ? s.result.times : []);
export const getReservedAppointment = createSelector(getQMaticState, s => s.reservedAppointment);
export const isLoadingNewAppointmentInfo = createSelector(getQMaticState, s =>
  [s.services, s.branches, s.dates, s.times, s.reservedAppointment, s.settings].some(status => status.state === CallStateType.LOADING));
export const getClientSettings = createSelector(getQMaticState, s => s.settings.result);


function parseService(service: QMaticService): QMaticParsedService {
  if (service?.custom) {
    try {
      return { ...service, parsedCustom: JSON.parse(service.custom) };
    } catch (e) {
      console.log(e);
    }
  }
  return { ...service, parsedCustom: {} };
}
