import { EMPTY_ARRAY, stateError, stateLoading, stateSuccess } from '../shared/call-state';
import { EventsActions, EventsActionTypes } from './events.actions';
import { EventsState, initialEventsState } from './events.state';

export function eventsReducer(state = initialEventsState, action: EventsActions): EventsState {
  switch (action.type) {
    case EventsActionTypes.GET_EVENTS:
      return {
        ...state,
        events: stateLoading(initialEventsState.events.result),
        filter: action.payload,
      };
    case EventsActionTypes.GET_EVENTS_SUCCESS:
      return {
        ...state,
        events: stateSuccess(action.payload),
        filter: { ...state.filter, cursor: action.payload.cursor },
      };
    case EventsActionTypes.GET_EVENTS_FAILED:
      return { ...state, events: stateError(action.error, state.events.result) };
    case EventsActionTypes.GET_MORE_EVENTS:
      return { ...state, events: stateLoading(state.events.result) };
    case EventsActionTypes.GET_MORE_EVENTS_SUCCESS:
      return {
        ...state,
        events: stateSuccess({
          ...action.payload,
          events: (state.events.result ? state.events.result.events : EMPTY_ARRAY).concat(action.payload.events),
        }),
        filter: { ...state.filter, cursor: action.payload.cursor },
      };
    case EventsActionTypes.GET_MORE_EVENTS_FAILED:
      return { ...state, events: stateError(action.error, state.events.result) };
    case EventsActionTypes.ADD_EVENT_TO_CALENDAR:
      return { ...state, addToCalendar: stateLoading(initialEventsState.addToCalendar.result) };
    case EventsActionTypes.ADD_EVENT_TO_CALENDAR_SUCCESS:
      return { ...state, addToCalendar: stateSuccess(action.payload) };
    case EventsActionTypes.ADD_EVENT_TO_CALENDAR_FAILED:
      return { ...state, addToCalendar: stateError(action.error, initialEventsState.addToCalendar.result) };
  }
  return state;
}
