import { ChangeDetectionStrategy, Component, OnDestroy, OnInit } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { Actions, ofType } from '@ngrx/effects';
import { select, Store } from '@ngrx/store';
import { Observable, Subscription } from 'rxjs';
import { filterNull } from '../../../ngrx';
import { ApiRequestStatus } from '../../../../../framework/client/rpc';
import {
  BackendsActionTypes,
  GetBackendRogerthatAppsAction,
  GetPaymentProviderAction,
  ListEmbeddedAppsAction,
  UpdatePaymentProviderAction,
} from '../../../actions';
import {
  getBackendPaymentProvider,
  getBackendPaymentProviderEditStatus,
  getBackendRogerthatApps,
  getEmbeddedApps,
} from '../../../console.state';
import { EmbeddedApp, EmbeddedAppTag, PaymentProvider, RogerthatApp } from '../../../interfaces';

@Component({
  selector: 'rcc-edit-payment-provider',
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <rcc-payment-provider-form [paymentProvider]="paymentProvider$ | async"
                               [status]="status$ | async"
                               [apps]="rogerthatApps$ | async"
                               [embeddedApplications]="embeddedApplications$ | async"
                               (save)="save($event)"></rcc-payment-provider-form>`,
})
export class EditPaymentProviderComponent implements OnInit, OnDestroy {
  paymentProvider$: Observable<PaymentProvider>;
  rogerthatApps$: Observable<RogerthatApp[]>;
  status$: Observable<ApiRequestStatus>;
  embeddedApplications$: Observable<EmbeddedApp[]>;
  private sub: Subscription;

  constructor(private store: Store,
              private actions$: Actions,
              private router: Router,
              private route: ActivatedRoute) {
  }

  ngOnInit() {
    this.store.dispatch(new GetBackendRogerthatAppsAction());
    this.store.dispatch(new GetPaymentProviderAction(this.route.snapshot.params.paymentProviderId));
    this.paymentProvider$ = this.store.pipe(select(getBackendPaymentProvider), filterNull());
    this.rogerthatApps$ = this.store.pipe(select(getBackendRogerthatApps));
    this.status$ = this.store.pipe(select(getBackendPaymentProviderEditStatus));
    this.sub = this.actions$.pipe(ofType(BackendsActionTypes.UPDATE_PAYMENT_PROVIDER_COMPLETE)).subscribe(() => {
      this.router.navigate([ '..' ], { relativeTo: this.route });
    });
    this.store.dispatch(new ListEmbeddedAppsAction(EmbeddedAppTag.PAYMENTS));
    this.embeddedApplications$ = this.store.pipe(select(getEmbeddedApps));
  }

  ngOnDestroy() {
    this.sub.unsubscribe();
  }

  save(paymentProvider: PaymentProvider) {
    this.store.dispatch(new UpdatePaymentProviderAction(paymentProvider));
  }
}
