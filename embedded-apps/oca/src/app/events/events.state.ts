import { createFeatureSelector, createSelector } from '@ngrx/store';
import { CallStateType, EMPTY_ARRAY, initialStateResult, ResultState } from '../shared/call-state';
import { GetEventsParams, OcaEvent, OcaEventList } from './events';

export const EVENTS_FEATURE = 'events';

export interface EventsState {
  events: ResultState<OcaEventList>;
  filter: GetEventsParams;
  addToCalendar: ResultState<{ message: string }>;
}

const getEventsState = createFeatureSelector<EventsState>(EVENTS_FEATURE);

export const initialEventsState: EventsState = {
  events: initialStateResult,
  filter: { startDate: '', endDate: '' },
  addToCalendar: initialStateResult,
};

export const getEvents = createSelector(getEventsState, s => s.events.result ? s.events.result.events : EMPTY_ARRAY);
export const eventsLoading = createSelector(getEventsState, s => s.events.state === CallStateType.LOADING);
export const getEventsFilter = createSelector(getEventsState, s => s.filter);
export const hasMoreEvents = createSelector(getEventsState, s => s.events.state === CallStateType.SUCCESS ? s.events.result.has_more : true);
export const getEventById = createSelector(getEvents, (events: OcaEvent[], id: number) => events.find(e => e.id === id));
export const isAddingToCalendar = createSelector(getEventsState, s => s.addToCalendar.state === CallStateType.LOADING);
