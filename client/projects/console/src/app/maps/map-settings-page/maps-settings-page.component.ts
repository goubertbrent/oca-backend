import { ChangeDetectionStrategy, Component, OnInit } from '@angular/core';
import { ActivatedRoute } from '@angular/router';
import { select, Store } from '@ngrx/store';
import { CallStateType, ResultState } from '@oca/web-shared';
import { Observable } from 'rxjs';
import { MapConfig, ReportsMapFilter } from '../maps';
import { GetMapConfigAction, SaveMapConfigAction } from '../maps.actions';
import { MapsState } from '../maps.reducer';
import { getMapConfig } from '../maps.selectors';

@Component({
  selector: 'rcc-maps-settings-page',
  templateUrl: './maps-settings-page.component.html',
  styleUrls: ['./maps-settings-page.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class MapsSettingsPageComponent implements OnInit {
  appId: string;
  mapConfig$: Observable<ResultState<MapConfig>>;
  filters = [
    { value: ReportsMapFilter.ALL, label: 'All' },
    { value: ReportsMapFilter.NEW, label: 'New' },
    { value: ReportsMapFilter.IN_PROGRESS, label: 'In progress' },
    { value: ReportsMapFilter.RESOLVED, label: 'Resolved' },
  ];
  LOADING = CallStateType.LOADING;

  constructor(private store: Store<MapsState>,
              private route: ActivatedRoute) {
  }

  ngOnInit() {
    this.appId = this.route.snapshot.params.appId;
    this.store.dispatch(GetMapConfigAction({ appId: this.appId }));
    this.mapConfig$ = this.store.pipe(select(getMapConfig));
  }

  onSaved($event: MapConfig) {
    this.store.dispatch(SaveMapConfigAction({ appId: this.appId, payload: $event }));
  }
}
