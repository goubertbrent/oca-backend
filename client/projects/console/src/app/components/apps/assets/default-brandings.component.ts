import { ChangeDetectionStrategy, Component, OnDestroy, OnInit } from '@angular/core';
import { Store } from '@ngrx/store';
import { Observable, Subscription } from 'rxjs';
import { filterNull } from '../../../ngrx';
import { ApiRequestStatus } from '../../../../../framework/client/rpc';
import * as actions from '../../../actions';
import { getApp, getDefaultBrandings, getDefaultBrandingsStatus } from '../../../console.state';
import { App, DefaultBranding } from '../../../interfaces';

@Component({
  selector: 'rcc-app-default-brandings',
  changeDetection: ChangeDetectionStrategy.OnPush,
  templateUrl: 'default-brandings.component.html',
})
export class AppDefaultBrandingsComponent implements OnInit, OnDestroy {
  app: App;
  brandings$: Observable<DefaultBranding[]>;
  status$: Observable<ApiRequestStatus>;
  private subscription: Subscription;

  constructor(private store: Store) {
  }

  public ngOnInit(): void {
    this.subscription = this.store.select(getApp).pipe(filterNull()).subscribe(app => {
      this.app = app;
      this.store.dispatch(new actions.GetDefaultBrandingsAction({ appId: app.app_id }));
    });
    this.brandings$ = this.store.select(getDefaultBrandings);
    this.status$ = this.store.select(getDefaultBrandingsStatus);
  }

  ngOnDestroy() {
    this.subscription.unsubscribe();
  }

  public removeBranding(branding: DefaultBranding) {
    this.store.dispatch(new actions.RemoveDefaultBrandingAction({ appId: this.app.app_id, data: branding }));
  }
}
