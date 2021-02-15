import { ChangeDetectionStrategy, Component, OnInit, ViewEncapsulation } from '@angular/core';
import { FormControl } from '@angular/forms';
import { select, Store } from '@ngrx/store';
import { CallStateType, NewsItem, ResultState } from '@oca/web-shared';
import { IFormControl } from '@rxweb/types';
import { combineLatest, EMPTY, Observable, timer } from 'rxjs';
import { debounce, distinctUntilChanged, map, take } from 'rxjs/operators';
import { GetGlobalConfigAction } from '../../../shared/shared.actions';
import { isShopUser } from '../../../shared/shared.state';
import { ServiceNewsGroup } from '../../news';
import { CopyNewsItemAction, DeleteNewsItemAction, GetNewsListAction } from '../../news.actions';
import {
  canEditFeaturedItems,
  canEditRss,
  getNewsCursor,
  getNewsItemListStatus,
  getNewsItems,
  getNewsOptions,
  hasMoreNews,
  initialNewsState,
  isNewsListLoading,
  NewsState,
} from '../../news.state';

@Component({
  selector: 'oca-news-list-page',
  templateUrl: './news-list-page.component.html',
  styleUrls: ['./news-list-page.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class NewsListPageComponent implements OnInit {
  newsList$: Observable<NewsItem[]>;
  hasMore$: Observable<boolean>;
  newsGroups$: Observable<ServiceNewsGroup[]>;
  isNewsListLoading$: Observable<boolean>;
  hasNoNews$: Observable<boolean>;
  hasNoResults: Observable<boolean>;
  canEditRss$: Observable<boolean>;
  canEditFeatured$: Observable<boolean>;
  searchControl = new FormControl() as IFormControl<string>;

  private listStatus$: Observable<ResultState<null>>;

  constructor(private store: Store<NewsState>) {
  }

  ngOnInit() {
    this.newsList$ = this.store.pipe(select(getNewsItems));
    this.hasMore$ = this.store.pipe(select(hasMoreNews));
    this.isNewsListLoading$ = this.listStatus$.pipe(select(isNewsListLoading));
    this.canEditRss$ = this.store.pipe(select(canEditRss));
    this.canEditFeatured$ = this.store.pipe(select(canEditFeaturedItems));
    this.store.pipe(select(getNewsItemListStatus)).pipe(take(1)).subscribe(status => {
      if (status === initialNewsState.listStatus) {
        this.store.dispatch(new GetNewsListAction({ cursor: null, query: null }));
      }
    });
    this.hasNoNews$ = combineLatest([this.isNewsListLoading$, this.newsList$]).pipe(
      map(([loading, newsList]) => !loading && newsList.length === 0),
    );
    this.newsGroups$ = this.store.pipe(select(getNewsOptions), map(o => o?.groups ?? []));
    this.searchControl.valueChanges.pipe(
      distinctUntilChanged(),
      // Debounce in case query is not empty, otherwise immediately send the request
      debounce(qry => qry ? timer(400) : EMPTY)).subscribe(query => {
      this.store.dispatch(new GetNewsListAction({ cursor: null, query }));
    });
  }

  onLoadMore() {
    this.store.pipe(select(getNewsCursor), take(1)).subscribe(cursor => this.store.dispatch(new GetNewsListAction({
      cursor,
      query: this.searchControl.value,
    })));
  }

  onDeleteItem(item: NewsItem) {
    this.store.dispatch(new DeleteNewsItemAction(item));
  }

  onCopyItem(item: NewsItem) {
    this.store.dispatch(new CopyNewsItemAction(item));
  }
}
