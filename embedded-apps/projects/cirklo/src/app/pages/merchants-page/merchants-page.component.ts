import { ChangeDetectionStrategy, Component, OnDestroy, OnInit, ViewChild } from '@angular/core';
import { IonInfiniteScroll } from '@ionic/angular';
import { select, Store } from '@ngrx/store';
import { Observable, Subject } from 'rxjs';
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
  hasMore$: Observable<boolean>;
  loading$: Observable<boolean>;
  private searchQuery: string | null = null;

  private destroyed$ = new Subject();

  constructor(private store: Store) {
  }

  ngOnInit() {
    this.store.dispatch(new GetMerchantsAction({}));
    this.merchants$ = this.store.pipe(select(getMerchants));
    this.loading$ = this.store.pipe(select(areMerchantsLoading));
    this.hasMore$ = this.store.pipe(select(hasMoreMerchants));
    this.loading$.pipe(takeUntil(this.destroyed$)).subscribe(loading => {
      if (!loading && !this.infiniteScroll.disabled) {
        this.infiniteScroll.complete();
      }
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
        this.store.dispatch(new GetMerchantsAction({ cursor, query: this.searchQuery }));
      }
    });
  }

  queryChanged(query: string) {
    this.searchQuery = query;
    this.store.dispatch(new GetMerchantsAction({ query }));
  }
}
