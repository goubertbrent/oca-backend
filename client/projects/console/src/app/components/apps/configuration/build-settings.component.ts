import { ChangeDetectionStrategy, Component, OnInit } from '@angular/core';
import { Store } from '@ngrx/store';
import { Observable } from 'rxjs';
import { filterNull } from '../../../ngrx';
import { ApiRequestStatus } from '../../../../../framework/client/rpc';
import { GetBuildSettingsAction, UpdateBuildSettingsAction } from '../../../actions';
import { getApp, getBuildSettings, getBuildSettingsStatus, updateBuildSettingsStatus } from '../../../console.state';
import { App, BuildSettings } from '../../../interfaces';

@Component({
  selector: 'rcc-build-settings',
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <rcc-build-settings-form [buildSettings]="buildSettings$ | async"
                             [app]="app$ | async"
                             [status]="status$ | async"
                             [updateStatus]="updateStatus$ | async"
                             (save)="save($event)"></rcc-build-settings-form>`,
})
export class BuildSettingsComponent implements OnInit {
  buildSettings$: Observable<BuildSettings>;
  app$: Observable<App>;
  status$: Observable<ApiRequestStatus>;
  updateStatus$: Observable<ApiRequestStatus>;

  constructor(private store: Store) {
  }

  ngOnInit() {
    this.buildSettings$ = this.store.select(getBuildSettings).pipe(filterNull());
    this.updateStatus$ = this.store.select(getBuildSettingsStatus);
    this.status$ = this.store.select(updateBuildSettingsStatus);
    this.app$ = <Observable<App>>this.store.select(getApp).pipe(filterNull());
    this.store.dispatch(new GetBuildSettingsAction());
  }

  save(buildSettings: BuildSettings) {
    this.store.dispatch(new UpdateBuildSettingsAction(buildSettings));
  }
}
