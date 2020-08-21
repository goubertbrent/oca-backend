import { Action } from '@ngrx/store';
import { ApiRequestStatus } from '../../../framework/client/rpc';
import { ReviewNotes } from '../interfaces';

export const enum ReviewNotesActionTypes {
  GET_REVIEW_NOTES_LIST = '[RCC:dev accounts] Get review notes list',
  GET_REVIEW_NOTES_LIST_COMPLETE = '[RCC:dev accounts] Get review notes list complete',
  GET_REVIEW_NOTES_LIST_FAILED = '[RCC:dev accounts] Get review notes list failed',
  CLEAR_REVIEW_NOTES = '[RCC:dev accounts] Clear review notes',
  GET_REVIEW_NOTES = '[RCC:dev accounts] Get review notes',
  GET_REVIEW_NOTES_COMPLETE = '[RCC:dev accounts] Get review notes complete',
  GET_REVIEW_NOTES_FAILED = '[RCC:dev accounts] Get review notes failed',
  CREATE_REVIEW_NOTES = '[RCC:dev accounts] Create review notes',
  CREATE_REVIEW_NOTES_COMPLETE = '[RCC:dev accounts] Create review notes complete',
  CREATE_REVIEW_NOTES_FAILED = '[RCC:dev accounts] Create review notes failed',
  UPDATE_REVIEW_NOTES = '[RCC:dev accounts] Update review notes',
  UPDATE_REVIEW_NOTES_COMPLETE = '[RCC:dev accounts] Update review notes complete',
  UPDATE_REVIEW_NOTES_FAILED = '[RCC:dev accounts] Update review notes failed',
  REMOVE_REVIEW_NOTES = '[RCC:dev accounts] Remove review notes',
  REMOVE_REVIEW_NOTES_COMPLETE = '[RCC:dev accounts] Remove review notes complete',
  REMOVE_REVIEW_NOTES_FAILED = '[RCC:dev accounts] Remove review notes failed',
}

export class GetReviewNotesListAction implements Action {
  readonly type = ReviewNotesActionTypes.GET_REVIEW_NOTES_LIST;
}

export class GetReviewNotesListCompleteAction implements Action {
  readonly type = ReviewNotesActionTypes.GET_REVIEW_NOTES_LIST_COMPLETE;

  constructor(public payload: Array<ReviewNotes>) {
  }
}

export class GetReviewNotesListFailedAction implements Action {
  readonly type = ReviewNotesActionTypes.GET_REVIEW_NOTES_LIST_FAILED;

  constructor(public payload: ApiRequestStatus) {
  }
}

export class ClearReviewNotesAction implements Action {
  readonly type = ReviewNotesActionTypes.CLEAR_REVIEW_NOTES;
}

export class GetReviewNotesAction implements Action {
  readonly type = ReviewNotesActionTypes.GET_REVIEW_NOTES;

  constructor(public payload: number) {
  }
}

export class GetReviewNotesCompleteAction implements Action {
  readonly type = ReviewNotesActionTypes.GET_REVIEW_NOTES_COMPLETE;

  constructor(public payload: ReviewNotes) {
  }
}

export class GetReviewNotesFailedAction implements Action {
  readonly type = ReviewNotesActionTypes.GET_REVIEW_NOTES_FAILED;

  constructor(public payload: ApiRequestStatus) {
  }
}

export class CreateReviewNotesAction implements Action {
  readonly type = ReviewNotesActionTypes.CREATE_REVIEW_NOTES;

  constructor(public payload: ReviewNotes) {
  }
}

export class CreateReviewNotesCompleteAction implements Action {
  readonly type = ReviewNotesActionTypes.CREATE_REVIEW_NOTES_COMPLETE;

  constructor(public payload: ReviewNotes) {
  }
}

export class CreateReviewNotesFailedAction implements Action {
  readonly type = ReviewNotesActionTypes.CREATE_REVIEW_NOTES_FAILED;

  constructor(public payload: ApiRequestStatus) {
  }
}

export class UpdateReviewNotesAction implements Action {
  readonly type = ReviewNotesActionTypes.UPDATE_REVIEW_NOTES;

  constructor(public payload: ReviewNotes) {
  }
}

export class UpdateReviewNotesCompleteAction implements Action {
  readonly type = ReviewNotesActionTypes.UPDATE_REVIEW_NOTES_COMPLETE;

  constructor(public payload: ReviewNotes) {
  }
}

export class UpdateReviewNotesFailedAction implements Action {
  readonly type = ReviewNotesActionTypes.UPDATE_REVIEW_NOTES_FAILED;

  constructor(public payload: ApiRequestStatus) {
  }
}

export class RemoveReviewNotesAction implements Action {
  readonly type = ReviewNotesActionTypes.REMOVE_REVIEW_NOTES;

  constructor(public payload: ReviewNotes) {
  }
}

export class RemoveReviewNotesCompleteAction implements Action {
  readonly type = ReviewNotesActionTypes.REMOVE_REVIEW_NOTES_COMPLETE;

  constructor(public payload: ReviewNotes) {
  }
}

export class RemoveReviewNotesFailedAction implements Action {
  readonly type = ReviewNotesActionTypes.REMOVE_REVIEW_NOTES_FAILED;

  constructor(public payload: ApiRequestStatus) {
  }
}

export type ReviewNotesActions
  = GetReviewNotesListAction
  | GetReviewNotesListCompleteAction
  | GetReviewNotesListFailedAction
  | GetReviewNotesAction
  | GetReviewNotesCompleteAction
  | GetReviewNotesFailedAction
  | ClearReviewNotesAction
  | CreateReviewNotesAction
  | CreateReviewNotesCompleteAction
  | CreateReviewNotesFailedAction
  | UpdateReviewNotesAction
  | UpdateReviewNotesCompleteAction
  | UpdateReviewNotesFailedAction
  | RemoveReviewNotesAction
  | RemoveReviewNotesCompleteAction
  | RemoveReviewNotesFailedAction;
