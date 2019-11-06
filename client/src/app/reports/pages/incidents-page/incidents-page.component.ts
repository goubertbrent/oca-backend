import { ChangeDetectionStrategy, Component, OnInit } from '@angular/core';
import { select, Store } from '@ngrx/store';
import { Observable } from 'rxjs';
import { GetIncidentsAction } from '../../reports.actions';
import { getIncidents, ReportsState } from '../../reports.state';
import { IncidentList } from '../reports';

@Component({
  selector: 'oca-incidents-page',
  templateUrl: './incidents-page.component.html',
  styleUrls: ['./incidents-page.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class IncidentsPageComponent implements OnInit {
  incidents$: Observable<IncidentList>;

  constructor(private store: Store<ReportsState>) {
  }

  ngOnInit() {
    this.store.dispatch(new GetIncidentsAction({ cursor: null }));
    this.incidents$ = this.store.pipe(select(getIncidents));
  }

  loadMoreIncidents($event: { cursor: string }) {
    this.store.dispatch(new GetIncidentsAction($event));
  }
}
