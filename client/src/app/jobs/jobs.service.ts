import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { select, Store } from '@ngrx/store';
import { Observable, of } from 'rxjs';
import { switchMap, withLatestFrom } from 'rxjs/operators';
import { RootState } from '../reducers';
import {
  EditJobOffer,
  JobOfferDetails,
  JobOfferList,
  JobSolicitationMessage,
  JobSolicitationMessageList,
  JobSolicitationsList,
  JobsSettings,
  NewSolicitationMessage,
} from './jobs';
import { getSolicitationMessages, hasSolicitationMessages } from './jobs.state';

@Injectable({ providedIn: 'root' })
export class JobsService {

  constructor(public http: HttpClient,
              public store: Store<RootState>) {
  }

  getJobOffersList(): Observable<JobOfferList> {
    return this.http.get<JobOfferList>('/common/jobs');
  }

  getJobOffer(jobId: number): Observable<JobOfferDetails> {
    return this.http.get<JobOfferDetails>(`/common/jobs/${jobId}`);
  }

  createJobOffer(payload: EditJobOffer): Observable<JobOfferDetails> {
    return this.http.post<JobOfferDetails>('/common/jobs', payload);
  }

  updateJobOffer(jobId: number, payload: EditJobOffer): Observable<JobOfferDetails> {
    return this.http.put<JobOfferDetails>(`/common/jobs/${jobId}`, payload);
  }

  getJobSolicitations(jobId: number): Observable<JobSolicitationsList> {
    return this.http.get<JobSolicitationsList>(`/common/jobs/${jobId}/solicitations`);
  }

  getSolicitationMessages(jobId: number, solicitationId: number): Observable<JobSolicitationMessageList> {
    return this.store.pipe(
      select(hasSolicitationMessages),
      withLatestFrom(this.store.pipe(select(getSolicitationMessages))),
      switchMap(([hasMessages, messages]) => {
        if (hasMessages) {
          const list: JobSolicitationMessageList = {
            results: messages,
          };
          return of(list);
        } else {
          return this.http.get<JobSolicitationMessageList>(`/common/jobs/${jobId}/solicitations/${solicitationId}/messages`);
        }
      }));
  }

  sendSolicitationMessage(jobId: number, solicitationId: number, message: NewSolicitationMessage): Observable<JobSolicitationMessage> {
    return this.http.post<JobSolicitationMessage>(`/common/jobs/${jobId}/solicitations/${solicitationId}/messages`, message);
  }

  getJobsSettings() {
    return this.http.get<JobsSettings>('/common/jobs/settings');
  }

  updateJobsSettings(payload: JobsSettings) {
    return this.http.put<JobsSettings>('/common/jobs/settings', payload);
  }
}
