import { ChangeDetectionStrategy, Component, OnInit } from '@angular/core';
import { Store } from '@ngrx/store';
import { Observable } from 'rxjs';
import { map, withLatestFrom } from 'rxjs/operators';

import { filterNull } from '../../../ngrx/index';
import { ApiRequestStatus } from '../../../../../framework/client/rpc';
import { PatchAppAction } from '../../../actions/apps.actions';
import { getApp, getAppsStatus, getRogerthatApp, getRogerthatAppStatus, patchAppStatus } from '../../../console.state';
import { App, PatchAppPayload, RogerthatApp } from '../../../interfaces/apps.interfaces';

@Component({
  selector: 'rcc-app-shared-configuration',
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <rcc-app-basic-configuration-form
      [app]="app$ | async"
      [rogerthatApp]="rogerthatApp$ | async"
      [status]="appStatus$ | async"
      [updateStatus]="updateStatus$ | async"
      (save)="submit($event)"></rcc-app-basic-configuration-form>`,
})
export class AppBasicConfigurationComponent implements OnInit {
  app$: Observable<App>;
  rogerthatApp$: Observable<RogerthatApp>;
  appStatus$: Observable<ApiRequestStatus>;
  updateStatus$: Observable<ApiRequestStatus>;
  payload: PatchAppPayload;

  constructor(private store: Store) {
  }

  ngOnInit() {
    this.app$ = this.store.select(getApp).pipe(filterNull());
    this.rogerthatApp$ = this.store.select(getRogerthatApp).pipe(filterNull());
    this.appStatus$ = this.store.select(getAppsStatus).pipe(
      withLatestFrom(this.store.select(getRogerthatAppStatus)),
      map(([ status1, status2 ]) => (<ApiRequestStatus>{
          success: status1.success && status2.success,
          loading: status1.loading || status2.loading,
          error: status1.error || status2.error,
        }),
      ));
    this.updateStatus$ = this.store.select(patchAppStatus);
  }

  submit(app: PatchAppPayload) {
    this.store.dispatch(new PatchAppAction(app));
  }

}
