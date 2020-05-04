import { createFeatureSelector, createSelector } from '@ngrx/store';
import { getRouteParams } from '../reducers';
import { CallStateType, initialStateResult, parseNumber, ResultState } from '../shared/util';
import {
  EditJobOffer,
  JobOffer,
  JobOfferDetails,
  JobOfferList,
  JobOfferStatistics,
  JobSolicitation,
  JobSolicitationMessage,
  JobSolicitationMessageList,
  JobSolicitationsList,
  JobsSettings,
  NewSolicitationMessage,
  UIJobSolicitationMessage,
} from './jobs';

export interface JobSolicitationsMessageStore {
  [ key: number ]: JobSolicitationMessageList;
}

export interface JobsState {
  jobOffersList: ResultState<JobOfferList>;
  jobOffer: ResultState<JobOffer | EditJobOffer>;
  jobOfferStats: ResultState<JobOfferStatistics>;
  solicitations: ResultState<JobSolicitationsList>;
  messages: JobSolicitationsMessageStore;
  solicitationMessagesLoading: boolean;
  newSolicitationMessage: ResultState<NewSolicitationMessage>;
  settings: ResultState<JobsSettings>;
}

export const initialState: JobsState = {
  jobOffersList: initialStateResult,
  jobOffer: initialStateResult,
  jobOfferStats: initialStateResult,
  solicitations: initialStateResult,
  messages: {},
  solicitationMessagesLoading: false,
  newSolicitationMessage: initialStateResult,
  settings: initialStateResult,
};

// Route-based selectors
export const getCurrentJobId = createSelector(getRouteParams, s => parseNumber(s.jobId));
export const getCurrentSolicitationId = createSelector(getRouteParams, s => s.solicitationId ? parseNumber(s.solicitationId) : null);


const featureSelector = createFeatureSelector<JobsState>('jobs');

export const getJobOffersList = createSelector(featureSelector, s => (s.jobOffersList.result?.results || []) as JobOfferDetails[]);
export const areJobOffersListLoading = createSelector(featureSelector, s => s.jobOffersList.state === CallStateType.LOADING);

export const getJobOffer = createSelector(featureSelector, s => s.jobOffer.result);
export const getJobOfferStats = createSelector(featureSelector, s => s.jobOfferStats.result);
export const isJobOfferLoading = createSelector(featureSelector, s => s.jobOffer.state === CallStateType.LOADING);

export const getSolicitations = createSelector(featureSelector, s => (s.solicitations.result?.results || []) as JobSolicitation[]);
export const areSolicitationsLoading = createSelector(featureSelector, s => s.solicitations.state === CallStateType.LOADING);
export const getHasNoSolicitations = createSelector(getSolicitations, areSolicitationsLoading, (solicitations, loading) =>
  !loading && solicitations.length === 0);
export const areSolicitationMessagesLoading = createSelector(featureSelector, s => s.solicitationMessagesLoading);
export const hasSolicitationMessages = createSelector(featureSelector, getCurrentSolicitationId, (state, id) => {
  return id && id in state.messages;
});
export const getSolicitationMessages = createSelector(featureSelector, getCurrentSolicitationId, (s, id) => {
  const messages: JobSolicitationMessage[] = id && id in s.messages ? s.messages[ id ].results : [];
  const mapped: UIJobSolicitationMessage[] = messages.map(convertToUIJobSolicitation);
  return mapped.sort((first, second) => {
    if (first.createDate > second.createDate) {
      return 1;
    }
    if (first.createDate < second.createDate) {
      return -1;
    }
    return 0;
  });
});

export const getCurrentSolicitation = createSelector(getSolicitations, getCurrentSolicitationId,
  (state, id) => state.find(s => s.id === id) || null);
export const isNewSolicitationMessageLoading = createSelector(featureSelector, s =>
  s.newSolicitationMessage.state === CallStateType.LOADING);
export const getNewSolicitationMessage = createSelector(featureSelector, s => s.newSolicitationMessage.result);
export const areJobSettingsLoading = createSelector(featureSelector, s => s.settings.state === CallStateType.LOADING);
export const getJobsSettings = createSelector(featureSelector, s => s.settings.result);


export function convertToUIJobSolicitation(message: JobSolicitationMessage){
  return {
    ...message,
    createDate: new Date(message.create_date),
  };
}
