import { Location } from '@angular/common';
import { ChangeDetectionStrategy, Component, OnInit, ViewEncapsulation } from '@angular/core';
import { ActivatedRoute } from '@angular/router';
import { select, Store } from '@ngrx/store';
import { Observable } from 'rxjs';
import { map } from 'rxjs/operators';
import { CallStateType, deepCopy, ResultState } from '../../../shared/util';
import { GetIncidentAction, UpdateIncidentAction } from '../../reports.actions';
import { getIncident, ReportsState } from '../../reports.state';
import { Incident } from '../reports';

@Component({
  selector: 'oca-edit-incident-page',
  templateUrl: './edit-incident-page.component.html',
  changeDetection: ChangeDetectionStrategy.OnPush,
  encapsulation: ViewEncapsulation.None,
})
export class EditIncidentPageComponent implements OnInit {
  incident$: Observable<ResultState<Incident>>;
  LOADING = CallStateType.LOADING;

  constructor(private store: Store<ReportsState>,
              private route: ActivatedRoute,
              private location: Location) {
  }

  ngOnInit() {
    const id: string = this.route.snapshot.params.id;
    this.store.dispatch(new GetIncidentAction({ id }));
    this.incident$ = this.store.pipe(select(getIncident), map(i => deepCopy(i)));
  }

  saveIncident(incident: Incident) {
    this.store.dispatch(new UpdateIncidentAction(incident));
  }

  backClicked() {
    this.location.back();
  }
}
