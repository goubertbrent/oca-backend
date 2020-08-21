import { insertItem, removeItem, updateItem } from '../ngrx';
import { apiRequestInitial, apiRequestLoading, apiRequestSuccess } from '../../../framework/client/rpc';
import { ReviewNotesActionTypes } from '../actions';
import { ReviewNotesActions } from '../actions/review-notes.actions';
import { initialReviewNotesState, IReviewNotesState } from '../states';

export function reviewNotesReducer(state: IReviewNotesState = initialReviewNotesState,
                                   action: ReviewNotesActions): IReviewNotesState {
  switch (action.type) {
    case ReviewNotesActionTypes.GET_REVIEW_NOTES_LIST:
      return {
        ...state,
        reviewNotesListStatus: apiRequestLoading,
      };
    case ReviewNotesActionTypes.GET_REVIEW_NOTES_LIST_COMPLETE:
      return {
        ...state,
        reviewNotesList: action.payload,
        reviewNotesListStatus: apiRequestSuccess,
      };
    case ReviewNotesActionTypes.GET_REVIEW_NOTES:
      return {
        ...state,
        getReviewNotesStatus: apiRequestLoading,
      };
    case ReviewNotesActionTypes.GET_REVIEW_NOTES_COMPLETE:
      return {
        ...state,
        reviewNotes: action.payload,
        getReviewNotesStatus: apiRequestSuccess,
      };
    case ReviewNotesActionTypes.GET_REVIEW_NOTES_FAILED:
      return {
        ...state,
        getReviewNotesStatus: action.payload,
      };
    case ReviewNotesActionTypes.CREATE_REVIEW_NOTES:
      return {
        ...state,
        createReviewNotesStatus: apiRequestLoading,
      };
    case ReviewNotesActionTypes.CREATE_REVIEW_NOTES_COMPLETE:
      return {
        ...state,
        reviewNotes: action.payload,
        createReviewNotesStatus: apiRequestSuccess,
        reviewNotesList: insertItem(state.reviewNotesList, action.payload),
      };
    case ReviewNotesActionTypes.CREATE_REVIEW_NOTES_FAILED:
      return {
        ...state,
        createReviewNotesStatus: action.payload,
      };
    case ReviewNotesActionTypes.UPDATE_REVIEW_NOTES:
      return {
        ...state,
        updateReviewNotesStatus: apiRequestLoading,
      };
    case ReviewNotesActionTypes.UPDATE_REVIEW_NOTES_COMPLETE:
      return {
        ...state,
        reviewNotes: action.payload,
        updateReviewNotesStatus: apiRequestSuccess,
        reviewNotesList: updateItem(state.reviewNotesList, action.payload, 'id'),
      };
    case ReviewNotesActionTypes.UPDATE_REVIEW_NOTES_FAILED:
      return {
        ...state,
        updateReviewNotesStatus: action.payload,
      };
    case ReviewNotesActionTypes.REMOVE_REVIEW_NOTES:
      return {
        ...state,
        removeReviewNotesStatus: apiRequestLoading,
      };
    case ReviewNotesActionTypes.REMOVE_REVIEW_NOTES_COMPLETE:
      return {
        ...state,
        reviewNotes: null,
        removeReviewNotesStatus: apiRequestSuccess,
        reviewNotesList: removeItem(state.reviewNotesList, action.payload, 'id'),
      };
    case ReviewNotesActionTypes.REMOVE_REVIEW_NOTES_FAILED:
      return {
        ...state,
        removeReviewNotesStatus: action.payload,
      };
    case ReviewNotesActionTypes.CLEAR_REVIEW_NOTES:
      return {
        ...state,
        reviewNotes: initialReviewNotesState.reviewNotes,
        createReviewNotesStatus: apiRequestInitial,
        updateReviewNotesStatus: apiRequestInitial,
        removeReviewNotesStatus: apiRequestInitial,
      };
    default:
      return state;
  }
}
