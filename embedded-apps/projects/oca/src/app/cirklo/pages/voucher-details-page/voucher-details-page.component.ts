import { ChangeDetectionStrategy, Component, OnDestroy, OnInit } from '@angular/core';
import { ActivatedRoute } from '@angular/router';
import { NavController } from '@ionic/angular';
import { Actions, ofType } from '@ngrx/effects';
import { select, Store } from '@ngrx/store';
import { combineLatest, Observable, Subject } from 'rxjs';
import { map, takeUntil } from 'rxjs/operators';
import { CirkloVoucher } from '../../cirklo';
import { CirkloActionTypes, ConfirmDeleteVoucherAction, DeleteVoucherSuccessAction } from '../../cirklo.actions';
import { getVoucher, getVouchersList } from '../../cirklo.selectors';

@Component({
  selector: 'app-voucher-details-page',
  templateUrl: './voucher-details-page.component.html',
  styleUrls: ['./voucher-details-page.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class VoucherDetailsPageComponent implements OnInit, OnDestroy {
  voucher$: Observable<CirkloVoucher | undefined>;
  logoUrl$: Observable<string | undefined>;
  voucherId: string;

  destroyed$ = new Subject();

  constructor(private store: Store,
              private route: ActivatedRoute,
              private navController: NavController,
              private actions$: Actions) {
  }

  ngOnInit() {
    this.voucherId = this.route.snapshot.params.id;
    this.voucher$ = this.store.pipe(select(getVoucher, this.voucherId));
    this.logoUrl$ = combineLatest([this.store.pipe(select(getVouchersList)), this.voucher$]).pipe(map(([list, voucher]) => {
      return list && voucher ? list.cities[ voucher.cityId ].logo_url : undefined;
    }));
    this.actions$.pipe(
      ofType<DeleteVoucherSuccessAction>(CirkloActionTypes.DELETE_VOUCHER_SUCCESS),
      takeUntil(this.destroyed$)).subscribe(() => {
      this.navController.back();
    });
  }

  ngOnDestroy() {
    this.destroyed$.next();
    this.destroyed$.complete();
  }

  deleteClicked() {
    this.store.dispatch(new ConfirmDeleteVoucherAction({ id: this.voucherId }));
  }
}
