import { ChangeDetectionStrategy, Component, OnDestroy, OnInit } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { Store } from '@ngrx/store';
import { TranslateService } from '@ngx-translate/core';
import { Observable, Subscription } from 'rxjs';
import { filter } from 'rxjs/operators';
import { DialogService } from '../../../../../framework/client/dialog';
import { ApiRequestStatus } from '../../../../../framework/client/rpc';
import * as actions from '../../../actions/index';
import * as states from '../../../console.state';
import { App, AppMetaData, AppTypes, BuildType, BulkUpdatePayload } from '../../../interfaces';

@Component({
  selector: 'rcc-bulk-update-apps',
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <rcc-bulk-update-form
      [apps]="apps$ | async"
      [bulkUpdateOptions]="bulkUpdateOptions"
      [defaultMetaData]="defaultMetaData$ | async"
      [defaultMetaDataStatus]="defaultMetaDataStatus$ | async"
      [appsStatus]="appsStatus$ | async"
      [updateStatus]="updateStatus$ | async"
      (start)="startBuilds($event)">
    </rcc-bulk-update-form>
  `,
})
export class BulkUpdateComponent implements OnInit, OnDestroy {
  bulkUpdateOptions: BulkUpdatePayload;
  apps$: Observable<App[]>;
  defaultMetaData$: Observable<AppMetaData[]>;
  defaultMetaDataStatus$: Observable<ApiRequestStatus>;
  appsStatus$: Observable<ApiRequestStatus>;
  updateStatus$: Observable<ApiRequestStatus>;

  private _sub: Subscription;

  constructor(private dialogService: DialogService,
              private route: ActivatedRoute,
              private router: Router,
              private store: Store,
              private translate: TranslateService) {
  }

  ngOnInit() {
    this.bulkUpdateOptions = {
      types: [ BuildType.IOS, BuildType.ANDROID ],
      release: true,
      generate_screenshots: false,
      app_ids: [],
      metadata: [],
    };
    this.store.dispatch(new actions.ClearBulkUpdateAction());
    this.store.dispatch(new actions.GetMetaDataDefaultsAction(AppTypes.ROGERTHAT));
    this.store.dispatch(new actions.GetProductionAppsAction());
    this.apps$ = <Observable<App[]>>this.store.select(states.getProductionApps);
    this.defaultMetaData$ = this.store.select(states.getDefaultMetaData);
    this.defaultMetaDataStatus$ = this.store.select(states.getAppMetaDataStatus);
    this.appsStatus$ = this.store.select(states.getProductionAppsStatus);
    this.updateStatus$ = this.store.select(states.getBulkUpdateStatus);
    this._sub = this.updateStatus$.pipe(filter(s => s.success)).subscribe(() => {
      this.dialogService.openAlert({
        title: this.translate.instant('rcc.bulk_update'),
        message: this.translate.instant('rcc.bulk_update_all_builds_scheduled'),
        ok: this.translate.instant('rcc.close'),
      });
      return this.router.navigate([ '..' ], { relativeTo: this.route });
    });
  }

  ngOnDestroy() {
    this._sub.unsubscribe();
  }

  startBuilds(options: BulkUpdatePayload) {
    this.store.dispatch(new actions.BulkUpdateAppsAction(options));
  }
}
