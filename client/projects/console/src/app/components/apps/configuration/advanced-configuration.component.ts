import { ChangeDetectionStrategy, Component, OnInit } from '@angular/core';
import { select, Store } from '@ngrx/store';
import { Observable } from 'rxjs';
import { filterNull } from '../../../ngrx';
import { ApiRequestStatus } from '../../../../../framework/client/rpc';
import { ListEmbeddedAppsAction, UpdateRogerthatAppAction } from '../../../actions';
import { getEmbeddedApps, getRogerthatApp, getRogerthatAppStatus } from '../../../console.state';
import { EmbeddedApp, RogerthatApp } from '../../../interfaces';

@Component({
  selector: 'rcc-app-advanced-configuration',
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <rcc-app-advanced-configuration-form
      [app]="app$ | async"
      [embeddedApps]="embeddedApplications$ | async"
      [status]="appStatus$ | async"
      (save)="save($event)">
    </rcc-app-advanced-configuration-form>`,
})
export class AppAdvancedConfigurationComponent implements OnInit {
  app$: Observable<RogerthatApp>;
  embeddedApplications$: Observable<EmbeddedApp[]>;
  appStatus$: Observable<ApiRequestStatus>;

  constructor(private store: Store) {
  }

  ngOnInit() {
    this.store.dispatch(new ListEmbeddedAppsAction());
    this.app$ = this.store.pipe(select(getRogerthatApp), filterNull());
    this.appStatus$ = this.store.pipe(select(getRogerthatAppStatus));
    this.embeddedApplications$ = this.store.pipe(select(getEmbeddedApps));
  }

  save(app: RogerthatApp) {
    this.store.dispatch(new UpdateRogerthatAppAction(app));
  }
}
