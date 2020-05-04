import { CallStateType, ResultState, stateError, stateLoading, stateSuccess, updateItem } from '../shared/util';
import {
  JobOfferList,
  JobOfferStatistics,
  JobSolicitation,
  JobSolicitationMessage,
  JobSolicitationsList,
  JobSolicitationStatus,
  JobStatus,
} from './jobs';
import { JobsActions, JobsActionTypes } from './jobs.actions';
import { initialState, JobSolicitationsMessageStore, JobsState } from './jobs.state';

function removeUnreadSolicitation(state: ResultState<JobOfferStatistics>, solicitationId: number) {
  if (state.state === CallStateType.SUCCESS) {
    return stateSuccess({ ...state.result, unread_solicitations: state.result.unread_solicitations.filter(id => id !== solicitationId) });
  }
  return state;
}

function updateJobOfferStats(state: ResultState<JobOfferStatistics>,
                             jobId: number,
                             statistics: JobOfferStatistics): ResultState<JobOfferStatistics> {
  if (state.result && state.result.id === jobId) {
    return { ...state, result: statistics };
  }
  return state;
}

function updateJobOfferListStatistic(state: ResultState<JobOfferList>,
                                     jobId: number,
                                     statistics: JobOfferStatistics): ResultState<JobOfferList> {
  if (state.result) {
    const newResults = [];
    for (const offer of state.result.results) {
      if (offer.offer.id === jobId) {
        newResults.push({ offer: offer.offer, statistics });
      } else {
        newResults.push(offer);
      }
    }
    return { ...state, result: { results: newResults } };
  }
  return state;
}

export function jobsReducer(state: JobsState = initialState, action: JobsActions): JobsState {
  switch (action.type) {
    case JobsActionTypes.GET_JOB_OFFER_LIST:
      return { ...state, jobOffersList: stateLoading(state.jobOffersList.result) };
    case JobsActionTypes.GET_JOB_OFFER_LIST_COMPLETE:
      return { ...state, jobOffersList: stateSuccess(action.payload) };
    case JobsActionTypes.GET_JOB_OFFER_LIST_FAILED:
      return { ...state, jobOffersList: stateError(action.error, state.jobOffersList.result) };
    case JobsActionTypes.GET_JOB_OFFER:
      return {
        ...state,
        jobOffer: stateLoading(initialState.jobOffer.result),
        jobOfferStats: stateLoading(initialState.jobOfferStats.result),
      };
    case JobsActionTypes.GET_JOB_OFFER_COMPLETE:
      return {
        ...state,
        jobOffer: stateSuccess(action.payload.offer),
        jobOfferStats: stateSuccess(action.payload.statistics),
      };
    case JobsActionTypes.GET_JOB_OFFER_FAILED:
      return { ...state, jobOffer: stateError(action.error, state.jobOffer.result) };
    case JobsActionTypes.CREATE_JOB_OFFER:
      return { ...state, jobOffer: stateLoading(action.payload) };
    case JobsActionTypes.CREATE_JOB_OFFER_COMPLETE:
      return {
        ...state,
        jobOffer: stateSuccess(action.payload.offer),
        jobOfferStats: stateSuccess(action.payload.statistics),
      };
    case JobsActionTypes.CREATE_JOB_OFFER_FAILED:
      return { ...state, jobOffer: stateError(action.error, state.jobOffer.result) };
    case JobsActionTypes.UPDATE_JOB_OFFER:
      return { ...state, jobOffer: stateLoading({ ...state.jobOffer.result, ...action.payload.offer }) };
    case JobsActionTypes.UPDATE_JOB_OFFER_COMPLETE:
      // Special case - job deleted, remove from state
      if (action.payload.offer.status === JobStatus.DELETED) {
        return { ...state, jobOffer: initialState.jobOffer };
      }
      return {
        ...state,
        jobOffer: stateSuccess(action.payload.offer),
        jobOfferStats: stateSuccess(action.payload.statistics),
      };
    case JobsActionTypes.UPDATE_JOB_OFFER_FAILED:
      return { ...state, jobOffer: stateError(action.error, state.jobOffer.result) };
    case JobsActionTypes.GET_SOLICITATIONS:
      return { ...state, solicitations: stateLoading(initialState.solicitations.result) };
    case JobsActionTypes.GET_SOLICITATIONS_COMPLETE:
      return { ...state, solicitations: stateSuccess(action.payload) };
    case JobsActionTypes.GET_SOLICITATIONS_FAILED:
      return { ...state, solicitations: stateError(action.error, state.solicitations.result) };
    case JobsActionTypes.GET_SOLICITATION_MESSAGES:
      return { ...state, solicitationMessagesLoading: true };
    case JobsActionTypes.GET_SOLICITATION_MESSAGES_COMPLETE:
      return {
        ...state,
        solicitationMessagesLoading: false,
        messages: { ...state.messages, [ action.payload.solicitationId ]: action.payload.messages },
        solicitations: updateSolicitations(state.solicitations, action.payload.solicitationId,
          { last_message: action.payload.messages.results[ action.payload.messages.results.length - 1 ] }),
        // Remove current solicitation from unread solicitations
        jobOfferStats: removeUnreadSolicitation(state.jobOfferStats, action.payload.solicitationId),
      };
    case JobsActionTypes.GET_SOLICITATION_MESSAGES_FAILED:
      return { ...state, solicitationMessagesLoading: false };
    case JobsActionTypes.SEND_SOLICITATION_MESSAGE:
      return { ...state, newSolicitationMessage: stateLoading(action.payload.message) };
    case JobsActionTypes.SEND_SOLICITATION_MESSAGE_COMPLETE:
      // Message send - reset new message and add to messages list
      return {
        ...state,
        newSolicitationMessage: initialState.newSolicitationMessage,
        messages: addMessageToSolicitations(state.messages, action.payload.solicitationId, action.payload.message),
        solicitations: updateSolicitations(state.solicitations, action.payload.solicitationId, {
          status: JobSolicitationStatus.STATUS_READ,
          last_message: action.payload.message,
        }),
        jobOfferStats: removeUnreadSolicitation(state.jobOfferStats, action.payload.solicitationId),
      };
    case JobsActionTypes.SEND_SOLICITATION_MESSAGE_FAILED:
      return { ...state, newSolicitationMessage: stateError(action.error, state.newSolicitationMessage.result) };
    case JobsActionTypes.GET_JOBS_SETTINGS:
      return { ...state, settings: stateLoading(initialState.settings.result) };
    case JobsActionTypes.GET_JOBS_SETTINGS_COMPLETE:
      return { ...state, settings: stateSuccess(action.payload) };
    case JobsActionTypes.GET_JOBS_SETTINGS_FAILED:
      return { ...state, settings: stateError(action.error, state.settings.result) };
    case JobsActionTypes.UPDATE_JOBS_SETTINGS:
      return { ...state, settings: stateLoading(action.payload) };
    case JobsActionTypes.UPDATE_JOBS_SETTINGS_COMPLETE:
      return { ...state, settings: stateSuccess(action.payload) };
    case JobsActionTypes.UPDATE_JOBS_SETTINGS_FAILED:
      return { ...state, settings: stateError(action.error, state.settings.result) };
    case JobsActionTypes.NEW_SOLICITATION_MESSAGE_RECEIVED:
      return {
        ...state,
        messages: addMessageToSolicitations(state.messages, action.payload.solicitation.id, action.payload.solicitation.last_message),
        solicitations: updateSolicitations(state.solicitations, action.payload.solicitation.id as number, action.payload.solicitation),
        jobOfferStats: updateJobOfferStats(state.jobOfferStats, action.payload.jobId, action.payload.statistics),
        jobOffersList: updateJobOfferListStatistic(state.jobOffersList, action.payload.jobId, action.payload.statistics),
      };
    case JobsActionTypes.SOLICITATION_UPDATED:
      return {
        ...state,
        solicitations: updateSolicitations(state.solicitations, action.payload.solicitationId, action.payload.solicitation),
      };
  }
  return state;
}

function addMessageToSolicitations(messages: JobSolicitationsMessageStore, solicitationId: number,
                                   newMessage: JobSolicitationMessage): JobSolicitationsMessageStore {
  if (!(solicitationId in messages)) {
    return messages;
  }
  if (messages[ solicitationId ].results.some(msg => msg.id === newMessage.id)) {
    // Sent by current user - ignore
    return messages;
  }
  return {
    ...messages,
    [ solicitationId ]: {
      results: [...messages[ solicitationId ].results, newMessage],
    },
  };
}


function updateSolicitations(solicitations: ResultState<JobSolicitationsList>,
                             solicitationId: number,
                             updated: Partial<JobSolicitation>): ResultState<JobSolicitationsList> {
  if (solicitations.result) {
    const solicitation = solicitations.result.results.find(s => s.id === solicitationId);
    if (solicitation) {
      const results = updateItem(solicitations.result.results, { ...solicitation, ...updated }, 'id');
      return { ...solicitations, result: { ...solicitations.result, results } };
    }
  }
  return solicitations;
}
