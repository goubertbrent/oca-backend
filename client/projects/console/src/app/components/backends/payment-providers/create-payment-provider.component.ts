import { ChangeDetectionStrategy, Component, OnDestroy, OnInit } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { Actions, ofType } from '@ngrx/effects';
import { select, Store } from '@ngrx/store';
import { Observable, Subscription } from 'rxjs';
import { ApiRequestStatus } from '../../../../../framework/client/rpc';
import { BackendsActionTypes, CreatePaymentProviderAction, GetBackendRogerthatAppsAction, ListEmbeddedAppsAction } from '../../../actions';
import { getBackendPaymentProviderEditStatus, getBackendRogerthatApps, getEmbeddedApps } from '../../../console.state';
import { EmbeddedApp, EmbeddedAppTag, PaymentProvider, RogerthatApp } from '../../../interfaces';

@Component({
  selector: 'rcc-create-payment-provider',
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <rcc-payment-provider-form [paymentProvider]="paymentProvider"
                               [embeddedApplications]="embeddedApplications$ | async"
                               [apps]="rogerthatApps$ | async"
                               [status]="status$ | async"
                               (save)="save($event)"></rcc-payment-provider-form>`,
})
export class CreatePaymentProviderComponent implements OnInit, OnDestroy {
  paymentProvider: PaymentProvider;
  rogerthatApps$: Observable<RogerthatApp[]>;
  embeddedApplications$: Observable<EmbeddedApp[]>;
  status$: Observable<ApiRequestStatus>;
  private sub: Subscription;

  constructor(private store: Store,
              private actions$: Actions,
              private router: Router,
              private route: ActivatedRoute) {
  }

  ngOnInit() {
    this.paymentProvider = {
      id: '',
      name: '',
      logo: null,
      description: '',
      black_white_logo: null,
      background_color: '#00a263',
      text_color: '#f4f4f4',
      button_color: 'dark',
      version: 1,
      oauth_settings: {
        client_id: '',
        secret: '',
        base_url: '',
        token_path: '',
        authorize_path: '',
        scope: '',
      },
      currencies: [],
      asset_types: [],
      settings: {},
      app_ids: [],
      embedded_application: null,
    };
    this.store.dispatch(new GetBackendRogerthatAppsAction());
    this.status$ = this.store.pipe(select(getBackendPaymentProviderEditStatus));
    this.rogerthatApps$ = this.store.pipe(select(getBackendRogerthatApps));
    this.sub = this.actions$.pipe(ofType(BackendsActionTypes.CREATE_PAYMENT_PROVIDER_COMPLETE)).subscribe(() => {
      this.router.navigate([ '..' ], { relativeTo: this.route });
    });
    this.store.dispatch(new ListEmbeddedAppsAction(EmbeddedAppTag.PAYMENTS));
    this.embeddedApplications$ = this.store.pipe(select(getEmbeddedApps));
  }

  ngOnDestroy() {
    this.sub.unsubscribe();
  }

  save(paymentProvider: PaymentProvider) {
    this.store.dispatch(new CreatePaymentProviderAction(paymentProvider));
  }
}
