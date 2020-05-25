import { ChangeDetectionStrategy, Component, OnDestroy, OnInit, ViewChild } from '@angular/core';
import { IonInfiniteScroll } from '@ionic/angular';
import { select, Store } from '@ngrx/store';
import { combineLatest, Observable, Subject } from 'rxjs';
import { take, takeUntil } from 'rxjs/operators';
import { CirkloMerchant } from '../../cirklo';
import { GetMerchantsAction } from '../../cirklo.actions';
import { areMerchantsLoading, getMerchants, getMerchantsCursor, hasMoreMerchants } from '../../cirklo.selectors';

@Component({
  selector: 'app-merchants-page',
  templateUrl: './merchants-page.component.html',
  styleUrls: ['./merchants-page.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class MerchantsPageComponent implements OnInit, OnDestroy {
  @ViewChild(IonInfiniteScroll, { static: true }) infiniteScroll: IonInfiniteScroll;
  merchants$: Observable<CirkloMerchant[]>;
  loading$: Observable<boolean>;

  private destroyed$ = new Subject();

  constructor(private store: Store) {
  }

  ngOnInit() {
    this.store.dispatch(new GetMerchantsAction({}));
    this.merchants$ = this.store.pipe(select(getMerchants));
    this.loading$ = this.store.pipe(select(areMerchantsLoading));
    combineLatest([this.store.pipe(select(hasMoreMerchants)), this.loading$]).pipe(takeUntil(this.destroyed$))
      .subscribe(([hasMore, loading]) => {
        if (!loading && !this.infiniteScroll.disabled) {
          this.infiniteScroll.complete();
        }
        this.infiniteScroll.disabled = !hasMore;
      });
  }

  ngOnDestroy() {
    this.destroyed$.next();
    this.destroyed$.complete();
  }

  trackById(index: number, merchant: CirkloMerchant) {
    return merchant.id;
  }

  loadMore() {
    this.store.pipe(select(getMerchantsCursor), take(1)).subscribe(cursor => {
      if (cursor) {
        this.store.dispatch(new GetMerchantsAction({ cursor }));
      }
    });
  }
}
