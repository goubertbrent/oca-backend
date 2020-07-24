import { ChangeDetectionStrategy, Component, OnInit } from '@angular/core';
import { select, Store } from '@ngrx/store';
import { CallStateType, ResultState } from '@oca/web-shared';
import { Observable } from 'rxjs';
import { isShopUser } from '../../../shared/shared.state';
import { MapConfig } from '../../maps';
import { GetMapConfigAction, SaveMapConfigAction } from '../../reports.actions';
import { getMapConfig, ReportsState } from '../../reports.state';
import { ReportsMapFilter } from '../reports';

@Component({
  selector: 'oca-reports-settings-page',
  templateUrl: './reports-settings-page.component.html',
  styleUrls: ['./reports-settings-page.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class ReportsSettingsPageComponent implements OnInit {
  isShopUser$: Observable<boolean>;
  mapConfig$: Observable<ResultState<MapConfig>>;
  filters = [
    { value: ReportsMapFilter.ALL, label: 'oca.All' },
    { value: ReportsMapFilter.NEW, label: 'oca.new' },
    { value: ReportsMapFilter.IN_PROGRESS, label: 'oca.in_progress' },
    { value: ReportsMapFilter.RESOLVED, label: 'oca.resolved' },
  ];
  LOADING = CallStateType.LOADING;

  constructor(private store: Store<ReportsState>) {
  }

  ngOnInit() {
    this.store.dispatch(new GetMapConfigAction());
    this.mapConfig$ = this.store.pipe(select(getMapConfig));
    this.isShopUser$ = this.store.pipe(select(isShopUser));
  }

  onSaved($event: MapConfig) {
    this.store.dispatch(new SaveMapConfigAction($event));
  }
}
