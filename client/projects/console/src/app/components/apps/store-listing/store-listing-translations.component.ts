import { ChangeDetectionStrategy, Component, OnInit } from '@angular/core';
import { ActivatedRoute, ActivatedRouteSnapshot } from '@angular/router';
import { Store } from '@ngrx/store';
import { Observable } from 'rxjs';
import { ApiRequestStatus } from '../../../../../framework/client/rpc';
import * as actions from '../../../actions/index';
import * as states from '../../../console.state';
import { AppMetaData } from '../../../interfaces';

@Component({
  selector: 'rcc-store-listing-translations',
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <rcc-store-listing-translations-form
      [appMetaData]="appMetaData$ | async"
      [appMetaDataStatus]="appMetaDataStatus$ | async"
      [updateAppMetaDataStatus]="updateAppMetaDataStatus$ | async"
      (update)="updateMetaData($event)">
    </rcc-store-listing-translations-form>`,
})
export class StoreListingTranslationsComponent implements OnInit {
  // Translated metadata component
  appId: string;
  appMetaData$: Observable<AppMetaData[]>;
  appMetaDataStatus$: Observable<ApiRequestStatus>;
  updateAppMetaDataStatus$: Observable<ApiRequestStatus>;

  constructor(private store: Store,
              private route: ActivatedRoute) {
  }

  ngOnInit() {
    this.appId = (<ActivatedRouteSnapshot>(<ActivatedRouteSnapshot>this.route.snapshot.parent).parent).params.appId;
    this.appMetaData$ = this.store.select(states.getAppMetaData);
    this.appMetaDataStatus$ = this.store.select(states.getAppMetaDataStatus);
    this.updateAppMetaDataStatus$ = this.store.select(states.getUpdateAppMetaDataStatus);

    this.store.dispatch(new actions.GetAppMetaDataAction(this.appId));
  }

  updateMetaData(metadata: AppMetaData) {
    this.store.dispatch(new actions.UpdateAppMetaDataAction(metadata, this.appId));
  }
}
