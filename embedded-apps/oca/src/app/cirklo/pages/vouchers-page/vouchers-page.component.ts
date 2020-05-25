import { animate, sequence, style, transition, trigger } from '@angular/animations';
import { ChangeDetectionStrategy, Component, OnDestroy, OnInit } from '@angular/core';
import { Actions, ofType } from '@ngrx/effects';
import { select, Store } from '@ngrx/store';
import { Observable, Subject } from 'rxjs';
import { map, take, takeUntil } from 'rxjs/operators';
import { RogerthatActionTypes, ScanQrCodeAction, ScanQrCodeUpdateAction } from '../../../rogerthat';
import { CirkloVoucher, CirkloVouchersList } from '../../cirklo';
import { AddVoucherAction, ConfirmDeleteVoucherAction, LoadVouchersAction } from '../../cirklo.actions';
import { getVouchersList, isVoucherListLoading } from '../../cirklo.selectors';

type LayoutNone = { layout: 'none'; } & CirkloVouchersList;
type LayoutSingular = { layout: 'singular', result: CirkloVoucher } & CirkloVouchersList;
type LayoutMultiple = { layout: 'multiple' } & CirkloVouchersList;
type Layout = { layout: null } | LayoutNone | LayoutSingular | LayoutMultiple;
const enum ItemAnimationState {
  ENABLED = 'enabled',
  DISABLED = 'disabled',
}
@Component({
  selector: 'app-vouchers-page',
  templateUrl: './vouchers-page.component.html',
  styleUrls: ['./vouchers-page.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
  animations: [
    trigger('cardAnimation', [
      // slide in from the bottom
      transition(`:enter`, [
        style({ transform: 'translateY(100%)', 'box-shadow': 'none', opacity: 0 }),
        sequence([
          animate('450ms cubic-bezier(0.4, 0.0, 0.2, 1)', style({})),
        ]),
      ]),
      // sweep to the right
      transition(':leave', [
        style({ height: '*', opacity: 1, transform: 'translateX(0)', 'box-shadow': '0 1px 4px 0 rgba(0, 0, 0, 0.3)' }),
        sequence([
          animate('.25s ease', style({ height: '*', opacity: .2, transform: 'translateX(20px)', 'box-shadow': 'none' })),
          animate('.1s ease', style({ height: 0, opacity: 0, transform: 'translateX(20px)', 'box-shadow': 'none' })),
        ])]),
    ]),
  ],
})
export class VouchersPageComponent implements OnInit, OnDestroy {
  voucherList$: Observable<CirkloVouchersList | null>;
  vouchers$: Observable<Layout>;
  showDeleteButton$: Observable<boolean>;
  isLoading$: Observable<boolean>;
  canDelete = false;
  itemAnimationState = ItemAnimationState.DISABLED;

  private destroyed$ = new Subject();

  constructor(private store: Store,
              private actions$: Actions) {
  }

  ngOnInit() {
    this.store.dispatch(new LoadVouchersAction());
    this.voucherList$ = this.store.pipe(select(getVouchersList));
    this.vouchers$ = this.voucherList$.pipe(map(list => {
      if (!list) {
        this.itemAnimationState = ItemAnimationState.DISABLED;
        return { layout: null };
      }
      setTimeout(() => {
        this.itemAnimationState = ItemAnimationState.ENABLED;
      }, 500);
      const results = list.results;
      switch (results.length) {
        case 0:
          return { layout: 'none', ...list } as LayoutNone;
        case 1:
          return { layout: 'singular', result: results[ 0 ], ...list } as LayoutSingular;
        default:
          return { layout: 'multiple', ...list };
      }
    }));
    this.showDeleteButton$ = this.vouchers$.pipe(map(vouchers => vouchers?.layout === 'singular' || vouchers?.layout === 'multiple'));
    this.isLoading$ = this.store.pipe(select(isVoucherListLoading));
    this.actions$.pipe(
      ofType<ScanQrCodeUpdateAction>(RogerthatActionTypes.SCAN_QR_CODE_UPDATE),
      takeUntil(this.destroyed$),
    ).subscribe(qrUpdate => {
      if (qrUpdate.payload.status === 'resolved') {
        this.qrScanned(qrUpdate.payload.content);
      }
    });
  }

  ngOnDestroy() {
    this.destroyed$.next();
    this.destroyed$.complete();
  }

  async confirmDelete(voucher: CirkloVoucher) {
    this.store.dispatch(new ConfirmDeleteVoucherAction({ id: voucher.id }));
  }

  deleteClicked() {
    this.vouchers$.pipe(take(1)).subscribe(vouchers => {
      if (vouchers.layout === 'singular') {
        this.confirmDelete(vouchers.result);
      } else if (vouchers.layout === 'multiple') {
        this.canDelete = !this.canDelete;
      }
    });
  }

  trackVouchers(index: number, voucher: CirkloVoucher) {
    return voucher.id;
  }

  startScanning() {
    this.store.dispatch(new ScanQrCodeAction('back'));
  }

  private qrScanned(content: string) {
    this.store.dispatch(new AddVoucherAction({ qrContent: content }));
  }
}
