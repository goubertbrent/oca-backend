import { ChangeDetectionStrategy, Component, OnDestroy, OnInit } from '@angular/core';
import { Store } from '@ngrx/store';
import { Observable, Subscription } from 'rxjs';
import { first } from 'rxjs/operators';
import { filterNull } from '../../../ngrx';
import { ApiRequestStatus } from '../../../../../framework/client/rpc';
import * as actions from '../../../actions/index';
import { getApp, getAppAssets, getAppAssetsStatus } from '../../../console.state';
import { App, AppAsset, AppDetailPayload } from '../../../interfaces';

@Component({
  selector: 'rcc-app-resources',
  changeDetection: ChangeDetectionStrategy.OnPush,
  templateUrl: 'app-resources.component.html',
})
export class AppResourcesComponent implements OnInit, OnDestroy {
  app$: Observable<App>;
  appAssets$: Observable<AppAsset[]>;
  status$: Observable<ApiRequestStatus>;
  private subscription: Subscription;

  constructor(private store: Store) {
  }

  public ngOnInit(): void {
    this.app$ = this.store.select(getApp).pipe(filterNull());
    this.subscription = this.app$.subscribe((app: App) => {
      const appDetails: AppDetailPayload = {
        appId: app.app_id,
      };
      this.store.dispatch(new actions.GetAppAssetsAction(appDetails));
    });
    this.appAssets$ = this.store.select(getAppAssets);
    this.status$ = this.store.select(getAppAssetsStatus);
  }

  ngOnDestroy() {
    this.subscription.unsubscribe();
  }

  public removeAsset(asset: AppAsset) {
    this.app$.pipe(first()).subscribe(app => {
      this.store.dispatch(new actions.RemoveAppAssetAction({ appId: app.app_id, data: asset }));
    });
  }
}
