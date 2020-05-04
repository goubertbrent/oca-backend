import { ChangeDetectionStrategy, Component, OnDestroy, OnInit } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { select, Store } from '@ngrx/store';
import { Observable, Subject } from 'rxjs';
import { filter, take, takeUntil, withLatestFrom } from 'rxjs/operators';
import { RootState } from '../../../reducers';
import { filterNull } from '../../../shared/util';
import { JobSolicitation, JobSolicitationStatus } from '../../jobs';
import { GetSolicitationsAction } from '../../jobs.actions';
import {
  areSolicitationsLoading,
  getCurrentJobId,
  getCurrentSolicitationId,
  getHasNoSolicitations,
  getSolicitations,
} from '../../jobs.state';

@Component({
  selector: 'oca-job-solicitations-list-page',
  templateUrl: './job-solicitations-list-page.component.html',
  styleUrls: ['./job-solicitations-list-page.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class JobSolicitationsListPageComponent implements OnInit, OnDestroy {
  loading$: Observable<boolean>;
  unread = JobSolicitationStatus.STATUS_UNREAD;
  solicitations$: Observable<JobSolicitation[]>;
  hasNoSolicitations$: Observable<boolean>;

  private destroyed$ = new Subject();

  constructor(private store: Store<RootState>,
              private router: Router,
              private route: ActivatedRoute) {
    this.store.pipe(select(getCurrentJobId), filterNull(), takeUntil(this.destroyed$))
      .subscribe(jobId => this.store.dispatch(new GetSolicitationsAction({ jobId })));
  }

  ngOnInit(): void {
    this.loading$ = this.store.pipe(select(areSolicitationsLoading));
    this.solicitations$ = this.store.pipe(select(getSolicitations));
    this.hasNoSolicitations$ = this.store.pipe(select(getHasNoSolicitations));

    // On page load, navigate to the first solicitation (if there are any)
    this.solicitations$.pipe(
      filter(list => list.length > 0),
      withLatestFrom(this.store.pipe(select(getCurrentSolicitationId))),
      takeUntil(this.destroyed$),
      take(1)).subscribe(([solicitations, solicitationId]) => {
      if (!solicitationId) {
        this.router.navigate([solicitations[ 0 ].id], { relativeTo: this.route });
      }
    });
  }

  ngOnDestroy() {
    this.destroyed$.next();
    this.destroyed$.complete();
  }
}
