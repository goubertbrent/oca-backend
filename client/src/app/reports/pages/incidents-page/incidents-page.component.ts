import { ChangeDetectionStrategy, Component, OnInit } from '@angular/core';
import { ActivatedRoute } from '@angular/router';
import { select, Store } from '@ngrx/store';
import { Observable, Subscription } from 'rxjs';
import { GetIncidentsAction } from '../../reports.actions';
import { getIncidents, incidentsLoading, ReportsState } from '../../reports.state';
import { IncidentList, IncidentStatus } from '../../reports';

@Component({
  selector: 'oca-incidents-page',
  templateUrl: './incidents-page.component.html',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class IncidentsPageComponent implements OnInit {
  incidents$: Observable<IncidentList>;
  loading$: Observable<boolean>;

  private currentStatus: IncidentStatus;
  private routeParamsSubscription: Subscription;

  constructor(private store: Store<ReportsState>,
              private route: ActivatedRoute) {
  }

  ngOnInit() {
    this.routeParamsSubscription = this.route.params.subscribe(params => {
      this.currentStatus = params.status;
      this.store.dispatch(new GetIncidentsAction({ status: this.currentStatus, cursor: null }));
    });
    this.incidents$ = this.store.pipe(select(getIncidents));
    this.loading$ = this.store.pipe(select(incidentsLoading));
  }

  loadMoreIncidents($event: { cursor: string }) {
    this.store.dispatch(new GetIncidentsAction({ status: this.currentStatus, cursor: $event.cursor }));
  }
}
