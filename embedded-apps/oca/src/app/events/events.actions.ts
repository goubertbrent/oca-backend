import { Action } from '@ngrx/store';
import { AddToCalendarParams, GetEventsParams, OcaEventList } from './events';

export const enum EventsActionTypes {
  GET_EVENTS = '[events] Get events',
  GET_EVENTS_SUCCESS = '[events] Get events complete',
  GET_EVENTS_FAILED = '[events] Get events failed',
  GET_MORE_EVENTS = '[events] Get more events',
  GET_MORE_EVENTS_SUCCESS = '[events] Get more events complete',
  GET_MORE_EVENTS_FAILED = '[events] Get more events failed',
  ADD_EVENT_TO_CALENDAR = '[events] Add event to calendar',
  ADD_EVENT_TO_CALENDAR_SUCCESS = '[events] Add event to calendar complete',
  ADD_EVENT_TO_CALENDAR_FAILED = '[events] Add event to calendar failed',
}

export class GetEventsAction implements Action {
  readonly type = EventsActionTypes.GET_EVENTS;

  constructor(public payload: GetEventsParams) {
  }
}

export class GetEventsSuccessAction implements Action {
  readonly type = EventsActionTypes.GET_EVENTS_SUCCESS;

  constructor(public payload: OcaEventList) {
  }
}

export class GetEventsFailedAction implements Action {
  readonly type = EventsActionTypes.GET_EVENTS_FAILED;

  constructor(public error: string) {
  }
}

export class GetMoreEventsAction implements Action {
  readonly type = EventsActionTypes.GET_MORE_EVENTS;

  constructor(public payload: GetEventsParams) {
  }
}

export class GetMoreEventsSuccessAction implements Action {
  readonly type = EventsActionTypes.GET_MORE_EVENTS_SUCCESS;

  constructor(public payload: OcaEventList) {
  }
}

export class GetMoreEventsFailedAction implements Action {
  readonly type = EventsActionTypes.GET_MORE_EVENTS_FAILED;

  constructor(public error: string) {
  }
}

export class AddEventToCalendarAction implements Action {
  readonly type = EventsActionTypes.ADD_EVENT_TO_CALENDAR;

  constructor(public payload: AddToCalendarParams) {
  }
}

export class AddEventToCalendarSuccessAction implements Action {
  readonly type = EventsActionTypes.ADD_EVENT_TO_CALENDAR_SUCCESS;

  constructor(public payload: { message: string }) {
  }
}

export class AddEventToCalendarFailedAction implements Action {
  readonly type = EventsActionTypes.ADD_EVENT_TO_CALENDAR_FAILED;

  constructor(public error: string) {
  }
}

export type EventsActions = GetEventsAction
  | GetEventsSuccessAction
  | GetEventsFailedAction
  | GetMoreEventsAction
  | GetMoreEventsSuccessAction
  | GetMoreEventsFailedAction
  | AddEventToCalendarAction
  | AddEventToCalendarSuccessAction
  | AddEventToCalendarFailedAction;

