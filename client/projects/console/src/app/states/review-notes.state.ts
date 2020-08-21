import { apiRequestInitial, ApiRequestStatus } from '../../../framework/client/rpc';
import { ReviewNotes } from '../interfaces';

export interface IReviewNotesState {
  reviewNotesList: ReviewNotes[];
  reviewNotesListStatus: ApiRequestStatus;
  reviewNotes: ReviewNotes | null;
  getReviewNotesStatus: ApiRequestStatus;
  createReviewNotesStatus: ApiRequestStatus;
  updateReviewNotesStatus: ApiRequestStatus;
  removeReviewNotesStatus: ApiRequestStatus;
}

export const initialReviewNotesState: IReviewNotesState = {
  reviewNotesList: [],
  reviewNotesListStatus: apiRequestInitial,
  reviewNotes: null,
  getReviewNotesStatus: apiRequestInitial,
  createReviewNotesStatus: apiRequestInitial,
  updateReviewNotesStatus: apiRequestInitial,
  removeReviewNotesStatus: apiRequestInitial,
};
