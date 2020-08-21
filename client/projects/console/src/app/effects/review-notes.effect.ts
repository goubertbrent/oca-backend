import { Injectable } from '@angular/core';
import { Actions, Effect, ofType } from '@ngrx/effects';
import { Store } from '@ngrx/store';
import { catchError, map, switchMap } from 'rxjs/operators';
import { handleApiError } from '../../../framework/client/rpc';
import * as actions from '../actions/review-notes.actions';
import { ReviewNotesService } from '../services';
import { IReviewNotesState } from '../states';

@Injectable()
export class ReviewNotesEffects {
  @Effect() getReviewNotesList$ = this.actions$.pipe(
    ofType<actions.GetReviewNotesListAction>(actions.ReviewNotesActionTypes.GET_REVIEW_NOTES_LIST),
    switchMap(() => this.reviewNotesService.getReviewNotesList().pipe(
      map(payload => new actions.GetReviewNotesListCompleteAction(payload)),
      catchError(error => handleApiError(actions.GetReviewNotesListFailedAction, error)),
    )));

  @Effect() addReviewNotes$ = this.actions$.pipe(
      ofType<actions.CreateReviewNotesAction>(actions.ReviewNotesActionTypes.CREATE_REVIEW_NOTES),
      switchMap(action => this.reviewNotesService.createReviewNotes(action.payload).pipe(
        map(payload => new actions.CreateReviewNotesCompleteAction(payload)),
        catchError(error => handleApiError(actions.CreateReviewNotesFailedAction, error)),
      )));

  @Effect() getReviewNotes$ = this.actions$.pipe(
      ofType<actions.GetReviewNotesAction>(actions.ReviewNotesActionTypes.GET_REVIEW_NOTES),
      switchMap(action => this.reviewNotesService.getReviewNotes(action.payload).pipe(
        map(payload => new actions.GetReviewNotesCompleteAction(payload)),
        catchError(error => handleApiError(actions.GetReviewNotesFailedAction, error)),
      )));

  @Effect() updateReviewNotes$ = this.actions$.pipe(
      ofType<actions.UpdateReviewNotesAction>(actions.ReviewNotesActionTypes.UPDATE_REVIEW_NOTES),
      switchMap(action => this.reviewNotesService.updateReviewNotes(action.payload).pipe(
        map(payload => new actions.UpdateReviewNotesCompleteAction(payload)),
        catchError(error => handleApiError(actions.UpdateReviewNotesFailedAction, error)),
      )));

  @Effect() removeReviewNotes$ = this.actions$.pipe(
      ofType<actions.RemoveReviewNotesAction>(actions.ReviewNotesActionTypes.REMOVE_REVIEW_NOTES),
      switchMap(action => this.reviewNotesService.removeReviewNotes(action.payload).pipe(
        map(payload => new actions.RemoveReviewNotesCompleteAction(payload)),
        catchError(error => handleApiError(actions.RemoveReviewNotesFailedAction, error)),
      )));

  constructor(private actions$: Actions<actions.ReviewNotesActions>,
              private store: Store<IReviewNotesState>,
              private reviewNotesService: ReviewNotesService) {
  }
}
