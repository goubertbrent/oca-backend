import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { map } from 'rxjs/operators';
import { ReviewNotes } from '../interfaces';
import { ConsoleConfig } from './console-config';

@Injectable()
export class ReviewNotesService {
  constructor(private http: HttpClient) {
  }

  getReviewNotesList() {
    return this.http.get<ReviewNotes[]>(`${ConsoleConfig.BUILDSERVER_API_URL}/review-notes`);
  }

  createReviewNotes(payload: ReviewNotes) {
    return this.http.post<ReviewNotes>(`${ConsoleConfig.BUILDSERVER_API_URL}/review-notes`, payload);
  }

  getReviewNotes(reviewNotesId: number) {
    return this.http.get<ReviewNotes>(`${ConsoleConfig.BUILDSERVER_API_URL}/review-notes/${reviewNotesId}`);
  }

  updateReviewNotes(payload: ReviewNotes) {
    return this.http.put<ReviewNotes>(`${ConsoleConfig.BUILDSERVER_API_URL}/review-notes/${payload.id}`, payload);
  }

  removeReviewNotes(payload: ReviewNotes) {
    return this.http.delete<ReviewNotes>(`${ConsoleConfig.BUILDSERVER_API_URL}/review-notes/${payload.id}`)
      .pipe(map(() => payload));
  }
}
