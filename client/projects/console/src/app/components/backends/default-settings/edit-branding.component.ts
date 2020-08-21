import { ChangeDetectionStrategy, Component, OnDestroy, OnInit } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { Store } from '@ngrx/store';
import { Observable, Subscription } from 'rxjs';
import { filterNull } from '../../../ngrx';
import { ApiRequestStatus } from '../../../../../framework/client/rpc';
import {
  ClearBackendBrandingAction,
  CreateBackendBrandingAction,
  GetBackendBrandingAction,
  UpdateBackendBrandingAction,
} from '../../../actions';
import { getBackendBranding, getBackendBrandingEditStatus, getBackendRogerthatApps } from '../../../console.state';
import { CreateDefaultBrandingPayload, DefaultBranding, RogerthatApp } from '../../../interfaces';

@Component({
  selector: 'rcc-edit-backend-branding',
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <rcc-app-branding
      [branding]="branding$ | async"
      [allowCreateDefault]="!edit"
      [apps]="apps$ | async"
      [edit]="edit"
      [status]="status$ | async"
      (save)="save($event)">
    </rcc-app-branding>`,
})
export class EditBackendBrandingComponent implements OnInit, OnDestroy {
  edit: boolean;
  branding$: Observable<DefaultBranding>;
  status$: Observable<ApiRequestStatus>;
  apps$: Observable<RogerthatApp[]>;
  private subscription: Subscription;

  constructor(private store: Store,
              private route: ActivatedRoute,
              private router: Router) {
  }

  ngOnInit() {
    const brandingId = this.route.snapshot.params[ 'brandingId' ];
    if (brandingId) {
      this.store.dispatch(new GetBackendBrandingAction(brandingId));
    } else {
      this.store.dispatch(new ClearBackendBrandingAction());
    }
    this.edit = !!brandingId;
    this.branding$ = this.store.select(getBackendBranding).pipe(filterNull());
    this.status$ = this.store.select(getBackendBrandingEditStatus);
    this.apps$ = this.store.select(getBackendRogerthatApps);
    this.subscription = this.store.select(getBackendBrandingEditStatus).subscribe((status: ApiRequestStatus) => {
      if (status.success) {
        // Redirect to resources overview
        this.router.navigate([ '..' ], { relativeTo: this.route });
      }
    });
  }

  ngOnDestroy() {
    this.subscription.unsubscribe();
  }

  save(branding: CreateDefaultBrandingPayload) {
    if (this.route.snapshot.params[ 'brandingId' ]) {
      this.store.dispatch(new UpdateBackendBrandingAction(branding));
    } else {
      this.store.dispatch(new CreateBackendBrandingAction(branding));
    }
  }
}
