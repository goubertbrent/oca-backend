import { Action } from '@ngrx/store';
import { ErrorAction } from '@oca/web-shared';
import {
  EditJobOffer,
  JobOfferDetails,
  JobOfferList,
  JobOfferStatistics,
  JobSolicitation,
  JobSolicitationMessage,
  JobSolicitationMessageList,
  JobSolicitationsList,
  JobsSettings,
  NewSolicitationMessage,
  PartialJobSolicitation,
} from './jobs';

export const enum JobsActionTypes {
  GET_JOB_OFFER_LIST = `[jobs] Get job offer list`,
  GET_JOB_OFFER_LIST_COMPLETE = '[jobs] Get job offer list complete',
  GET_JOB_OFFER_LIST_FAILED = '[jobs] Get job offer list failed',
  GET_JOB_OFFER = '[jobs] Get job offer',
  GET_JOB_OFFER_COMPLETE = '[jobs] Get job offer complete',
  GET_JOB_OFFER_FAILED = '[jobs] Get job offer failed',
  CREATE_JOB_OFFER = '[jobs] Create job offer',
  CREATE_JOB_OFFER_COMPLETE = '[jobs] Create job offer complete',
  CREATE_JOB_OFFER_FAILED = '[jobs] Create job offer failed',
  UPDATE_JOB_OFFER = '[jobs] Update job offer',
  UPDATE_JOB_OFFER_COMPLETE = '[jobs] Update job offer complete',
  UPDATE_JOB_OFFER_FAILED = '[jobs] Update job offer failed',
  GET_SOLICITATIONS = '[jobs] Get solicitations',
  GET_SOLICITATIONS_COMPLETE = '[jobs] Get solicitations complete',
  GET_SOLICITATIONS_FAILED = '[jobs] Get solicitations failed',
  GET_SOLICITATION_MESSAGES = '[jobs] Get solicitation messages',
  GET_SOLICITATION_MESSAGES_COMPLETE = '[jobs] Get solicitation messages complete',
  GET_SOLICITATION_MESSAGES_FAILED = '[jobs] Get solicitation messages failed',
  SEND_SOLICITATION_MESSAGE = '[jobs] Send solicitation message',
  SEND_SOLICITATION_MESSAGE_COMPLETE = '[jobs] Send solicitation message complete',
  SEND_SOLICITATION_MESSAGE_FAILED = '[jobs] Send solicitation message failed',
  GET_JOBS_SETTINGS = '[jobs] Get jobs settings',
  GET_JOBS_SETTINGS_COMPLETE = '[jobs] Get jobs settings complete',
  GET_JOBS_SETTINGS_FAILED = '[jobs] Get jobs settings failed',
  UPDATE_JOBS_SETTINGS = '[jobs] Update jobs settings',
  UPDATE_JOBS_SETTINGS_COMPLETE = '[jobs] Update jobs settings complete',
  UPDATE_JOBS_SETTINGS_FAILED = '[jobs] Update jobs settings failed',
  // Following actions are sent by server, received via firebase channel
  NEW_SOLICITATION_MESSAGE_RECEIVED = '[jobs] New solicitation message received',
  SOLICITATION_UPDATED = '[jobs] Solicitation updated',
}

export class GetJobOfferListAction implements Action {
  readonly type = JobsActionTypes.GET_JOB_OFFER_LIST;
}

export class GetJobOfferListCompleteAction implements Action {
  readonly type = JobsActionTypes.GET_JOB_OFFER_LIST_COMPLETE;

  constructor(public payload: JobOfferList) {
  }
}

export class GetJobOfferListFailedAction implements ErrorAction {
  readonly type = JobsActionTypes.GET_JOB_OFFER_LIST_FAILED;

  constructor(public error: string) {
  }
}

export class GetJobOfferAction implements Action {
  readonly type = JobsActionTypes.GET_JOB_OFFER;

  constructor(public payload: { jobId: number }) {
  }
}

export class GetJobOfferCompleteAction implements Action {
  readonly type = JobsActionTypes.GET_JOB_OFFER_COMPLETE;

  constructor(public payload: JobOfferDetails) {
  }
}

export class GetJobOfferFailedAction implements ErrorAction {
  readonly type = JobsActionTypes.GET_JOB_OFFER_FAILED;

  constructor(public error: string) {
  }
}

export class CreateJobOfferAction implements Action {
  readonly type = JobsActionTypes.CREATE_JOB_OFFER;

  constructor(public payload: EditJobOffer) {
  }
}

export class CreateJobOfferCompleteAction implements Action {
  readonly type = JobsActionTypes.CREATE_JOB_OFFER_COMPLETE;

  constructor(public payload: JobOfferDetails) {
  }
}

export class CreateJobOfferFailedAction implements ErrorAction {
  readonly type = JobsActionTypes.CREATE_JOB_OFFER_FAILED;

  constructor(public error: string) {
  }
}

export class UpdateJobOfferAction implements Action {
  readonly type = JobsActionTypes.UPDATE_JOB_OFFER;

  constructor(public payload: { id: number; offer: EditJobOffer }) {
  }
}

export class UpdateJobOfferCompleteAction implements Action {
  readonly type = JobsActionTypes.UPDATE_JOB_OFFER_COMPLETE;

  constructor(public payload: JobOfferDetails) {
  }
}

export class UpdateJobOfferFailedAction implements ErrorAction {
  readonly type = JobsActionTypes.UPDATE_JOB_OFFER_FAILED;

  constructor(public error: string) {
  }
}

export class GetSolicitationsAction implements Action {
  readonly type = JobsActionTypes.GET_SOLICITATIONS;

  constructor(public payload: { jobId: number }) {
  }
}

export class GetSolicitationsCompleteAction implements Action {
  readonly type = JobsActionTypes.GET_SOLICITATIONS_COMPLETE;

  constructor(public payload: JobSolicitationsList) {
  }
}

export class GetSolicitationsFailedAction implements ErrorAction {
  readonly type = JobsActionTypes.GET_SOLICITATIONS_FAILED;

  constructor(public error: string) {
  }
}

export class GetSolicitationMessagesAction implements Action {
  readonly type = JobsActionTypes.GET_SOLICITATION_MESSAGES;

  constructor(public payload: { jobId: number, solicitationId: number }) {
  }
}

export class GetSolicitationMessagesCompleteAction implements Action {
  readonly type = JobsActionTypes.GET_SOLICITATION_MESSAGES_COMPLETE;

  constructor(public payload: { solicitationId: number, messages: JobSolicitationMessageList }) {
  }
}

export class GetSolicitationMessagesFailedAction implements ErrorAction {
  readonly type = JobsActionTypes.GET_SOLICITATION_MESSAGES_FAILED;

  constructor(public error: string) {
  }
}

export class SendSolicitationMessageAction implements Action {
  readonly type = JobsActionTypes.SEND_SOLICITATION_MESSAGE;

  constructor(public payload: { jobId: number, solicitationId: number, message: NewSolicitationMessage }) {
  }
}

export class SendSolicitationMessageCompleteAction implements Action {
  readonly type = JobsActionTypes.SEND_SOLICITATION_MESSAGE_COMPLETE;

  constructor(public payload: { solicitationId: number; message: JobSolicitationMessage }) {
  }
}

export class SendSolicitationMessageFailedAction implements ErrorAction {
  readonly type = JobsActionTypes.SEND_SOLICITATION_MESSAGE_FAILED;

  constructor(public error: string) {
  }
}

export class GetJobSettingsAction implements Action {
  readonly type = JobsActionTypes.GET_JOBS_SETTINGS;
}

export class GetJobSettingsCompleteAction implements Action {
  readonly type = JobsActionTypes.GET_JOBS_SETTINGS_COMPLETE;

  constructor(public payload: JobsSettings) {
  }
}

export class GetJobSettingsFailedAction implements ErrorAction {
  readonly type = JobsActionTypes.GET_JOBS_SETTINGS_FAILED;

  constructor(public error: string) {
  }
}

export class UpdateJobSettingsAction implements Action {
  readonly type = JobsActionTypes.UPDATE_JOBS_SETTINGS;

  constructor(public payload: JobsSettings) {
  }
}

export class UpdateJobSettingsCompleteAction implements Action {
  readonly type = JobsActionTypes.UPDATE_JOBS_SETTINGS_COMPLETE;

  constructor(public payload: JobsSettings) {
  }
}

export class UpdateJobSettingsFailedAction implements ErrorAction {
  readonly type = JobsActionTypes.UPDATE_JOBS_SETTINGS_FAILED;

  constructor(public error: string) {
  }
}

/**
 * This action is only received from the server, not manually invoked on the client
 */
export class NewJobSolicitationMessageReceivedAction implements Action {
  readonly type = JobsActionTypes.NEW_SOLICITATION_MESSAGE_RECEIVED;

  constructor(public payload: { jobId: number; solicitation: PartialJobSolicitation; statistics: JobOfferStatistics }) {
  }
}

/**
 * This action is only received from the server, not manually invoked on the client
 */
export class SolicitationUpdatedAction implements Action {
  readonly type = JobsActionTypes.SOLICITATION_UPDATED;

  constructor(public payload: { jobId: number; solicitationId: number; solicitation: Partial<JobSolicitation>; }) {
  }
}

export type JobsActions = GetJobOfferListAction
  | GetJobOfferListCompleteAction
  | GetJobOfferListFailedAction
  | GetJobOfferAction
  | GetJobOfferCompleteAction
  | GetJobOfferFailedAction
  | CreateJobOfferAction
  | CreateJobOfferCompleteAction
  | CreateJobOfferFailedAction
  | UpdateJobOfferAction
  | UpdateJobOfferCompleteAction
  | UpdateJobOfferFailedAction
  | GetSolicitationsAction
  | GetSolicitationsCompleteAction
  | GetSolicitationsFailedAction
  | GetSolicitationMessagesAction
  | GetSolicitationMessagesCompleteAction
  | GetSolicitationMessagesFailedAction
  | SendSolicitationMessageAction
  | SendSolicitationMessageCompleteAction
  | SendSolicitationMessageFailedAction
  | GetJobSettingsAction
  | GetJobSettingsCompleteAction
  | GetJobSettingsFailedAction
  | UpdateJobSettingsAction
  | UpdateJobSettingsCompleteAction
  | UpdateJobSettingsFailedAction
  | NewJobSolicitationMessageReceivedAction
  | SolicitationUpdatedAction;
