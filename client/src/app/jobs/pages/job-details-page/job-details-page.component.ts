import { ChangeDetectionStrategy, Component, OnDestroy, OnInit } from '@angular/core';
import { ActivatedRoute } from '@angular/router';
import { select, Store } from '@ngrx/store';
import { Observable, Subject } from 'rxjs';
import { RootState } from '../../../reducers';
import { filterNull } from '../../../shared/util';
import { JobOffer, JobOfferStatistics } from '../../jobs';
import { getJobOffer, getJobOfferStats } from '../../jobs.state';

@Component({
  selector: 'oca-job-details-page',
  templateUrl: './job-details-page.component.html',
  styles: [`:host {
    display: flex;
    flex-direction: column;
    flex: 1;
  }`],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class JobDetailsPageComponent implements OnInit, OnDestroy {
  jobOffer$: Observable<JobOffer>;
  jobOfferStats$: Observable<JobOfferStatistics>;

  private destroyed$ = new Subject();

  constructor(private route: ActivatedRoute,
              private store: Store<RootState>) {
  }

  ngOnInit(): void {
    this.jobOffer$ = this.store.pipe(select(getJobOffer), filterNull()) as Observable<JobOffer>;
    this.jobOfferStats$ = this.store.pipe(select(getJobOfferStats), filterNull()) as Observable<JobOfferStatistics>;
  }

  ngOnDestroy(): void {
    this.destroyed$.next();
    this.destroyed$.complete();
  }
}
