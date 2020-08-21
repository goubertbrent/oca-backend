import { ChangeDetectionStrategy, Component, OnInit, ViewEncapsulation } from '@angular/core';
import { Store } from '@ngrx/store';
import { TranslateService } from '@ngx-translate/core';
import { Observable } from 'rxjs';
import { DialogService } from '../../../../../framework/client/dialog';
import { ApiRequestStatus } from '../../../../../framework/client/rpc';
import { GetPaymentProvidersAction, RemovePaymentProviderAction } from '../../../actions';
import { getBackendPaymentProviders, getBackendPaymentProvidersStatus } from '../../../console.state';
import { PaymentProvider } from '../../../interfaces';

@Component({
  selector: 'rcc-payment-providers-list',
  changeDetection: ChangeDetectionStrategy.OnPush,
  encapsulation: ViewEncapsulation.Emulated,
  templateUrl: 'payment-providers-list.component.html',
  styles: [`.payment-provider-card {
    width: 200px;
    display: inline-block;
  }`],
})

export class PaymentProvidersListComponent implements OnInit {
  paymentProviders$: Observable<PaymentProvider[]>;
  status$: Observable<ApiRequestStatus>;

  constructor(private store: Store,
              private translate: TranslateService,
              private dialogService: DialogService) {
  }

  ngOnInit() {
    this.store.dispatch(new GetPaymentProvidersAction());
    this.paymentProviders$ = this.store.select(getBackendPaymentProviders);
    this.status$ = this.store.select(getBackendPaymentProvidersStatus);
  }

  confirmRemove(paymentProvider: PaymentProvider) {
    const config = {
      title: this.translate.instant('rcc.remove_payment_provider'),
      message: this.translate.instant('rcc.are_you_sure_you_want_to_remove_payment_provider', { provider: paymentProvider.id }),
      ok: this.translate.instant('rcc.yes'),
      cancel: this.translate.instant('rcc.no'),
    };
    this.dialogService.openConfirm(config).afterClosed().subscribe((confirmed: boolean) => {
      if (confirmed) {
        this.store.dispatch(new RemovePaymentProviderAction((paymentProvider)));
      }
    });
  }
}
