import { ChangeDetectionStrategy, Component, OnDestroy, OnInit } from '@angular/core';
import { select, Store } from '@ngrx/store';
import { Observable, Subscription } from 'rxjs';
import { first } from 'rxjs/operators';
import { filterNull } from '../../../ngrx';
import { ApiRequestStatus } from '../../../../../framework/client/rpc';
import { GetAppSettingsAction, UpdateAppSettingsAction } from '../../../actions';
import { getApp, getAppSettings, getAppSettingsStatus, updateAppSettingsStatus } from '../../../console.state';
import { App, AppSettings } from '../../../interfaces';

@Component({
  selector: 'rcc-app-settings',
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <rcc-app-settings-form [appSettings]="appSettings$ | async"
                           [status]="status$ | async"
                           [updateStatus]="updateStatus$ | async"
                           (save)="save($event)"></rcc-app-settings-form>`,
})
export class AppSettingsComponent implements OnInit, OnDestroy {
  appSettings$: Observable<AppSettings>;
  status$: Observable<ApiRequestStatus>;
  updateStatus$: Observable<ApiRequestStatus>;

  private _appSubscription: Subscription;

  constructor(private store: Store) {
  }

  ngOnInit() {
    this.appSettings$ = this.store.pipe(select(getAppSettings), filterNull());
    this.status$ = this.store.pipe(select(getAppSettingsStatus));
    this.updateStatus$ = this.store.pipe(select(updateAppSettingsStatus));
    this._appSubscription = this.store.pipe(select(getApp), filterNull(), first())
      .subscribe((app: App) => this.store.dispatch(new GetAppSettingsAction({ appId: app.app_id })));
  }

  ngOnDestroy() {
    this._appSubscription.unsubscribe();
  }

  save(appSettings: AppSettings) {
    this.store.dispatch(new UpdateAppSettingsAction(appSettings));
  }
}
