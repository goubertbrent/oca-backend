import { ChangeDetectionStrategy, Component, OnDestroy, OnInit } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { Store } from '@ngrx/store';
import { Observable, Subscription } from 'rxjs';
import { filterNull } from '../../../ngrx';
import { ApiRequestStatus } from '../../../../../framework/client/rpc';
import {
  ClearBackendAppAssetAction,
  CreateBackendAppAssetAction,
  GetBackendAppAssetAction,
  UpdateBackendAppAssetAction,
} from '../../../actions';
import { getBackendAppAsset, getBackendAppAssetEditStatus, getBackendRogerthatApps } from '../../../console.state';
import { AppAsset, EditAppAssetPayload, RogerthatApp } from '../../../interfaces';

@Component({
  selector: 'rcc-backend-edit-resource',
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <rcc-app-resource [asset]="asset$ | async"
                      [status]="status$ |async"
                      [apps]="apps$ | async"
                      [edit]="edit"
                      [allowCreateDefault]="!edit"
                      (save)="save($event)"></rcc-app-resource>`,
})
export class EditBackendResourceComponent implements OnInit, OnDestroy {
  edit: boolean;
  asset$: Observable<AppAsset>;
  status$: Observable<ApiRequestStatus>;
  apps$: Observable<RogerthatApp[]>;
  private subscription: Subscription;

  constructor(private store: Store,
              private route: ActivatedRoute,
              private router: Router) {
  }

  ngOnInit() {
    const resourceId = this.route.snapshot.params[ 'resourceId' ];
    if (resourceId) {
      this.store.dispatch(new GetBackendAppAssetAction(resourceId));
    } else {
      this.store.dispatch(new ClearBackendAppAssetAction());
    }
    this.edit = !!resourceId;
    this.asset$ = this.store.select(getBackendAppAsset).pipe(filterNull());
    this.status$ = this.store.select(getBackendAppAssetEditStatus);
    this.apps$ = this.store.select(getBackendRogerthatApps);
    this.subscription = this.store.select(getBackendAppAssetEditStatus).subscribe((status: ApiRequestStatus) => {
        if (status.success) {
          // Redirect to resources overview
          this.router.navigate(['..'], { relativeTo: this.route });
        }
      },
    );
  }

  ngOnDestroy() {
    this.subscription.unsubscribe();
  }

  save(asset: EditAppAssetPayload) {
    if (this.route.snapshot.params[ 'resourceId' ]) {
      this.store.dispatch(new UpdateBackendAppAssetAction(asset));
    } else {
      this.store.dispatch(new CreateBackendAppAssetAction(asset));
    }
  }
}
