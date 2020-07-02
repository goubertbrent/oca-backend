import { ChangeDetectionStrategy, Component, OnInit } from '@angular/core';
import { ActivatedRoute } from '@angular/router';
import { select, Store } from '@ngrx/store';
import { Observable } from 'rxjs';
import { VoucherTransaction } from '../../cirklo';
import { GetVoucherTransactionsAction } from '../../cirklo.actions';
import { areTransactionsLoading, getVoucherTransactions } from '../../cirklo.selectors';

@Component({
  selector: 'app-voucher-transactions-page',
  templateUrl: './voucher-transactions-page.component.html',
  styleUrls: ['./voucher-transactions-page.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class VoucherTransactionsPageComponent implements OnInit {
  id: string;
  transactions$: Observable<VoucherTransaction[]>;
  loading$: Observable<boolean>;

  constructor(private store: Store,
              private route: ActivatedRoute) {
  }

  ngOnInit() {
    this.id = this.route.snapshot.params.id;
    this.store.dispatch(new GetVoucherTransactionsAction({ id: this.id }));
    this.transactions$ = this.store.pipe(select(getVoucherTransactions));
    this.loading$ = this.store.pipe(select(areTransactionsLoading));
  }

}
