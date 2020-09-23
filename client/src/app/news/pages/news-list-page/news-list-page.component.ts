import { ChangeDetectionStrategy, Component, OnInit, ViewEncapsulation } from '@angular/core';
import { select, Store } from '@ngrx/store';
import { NewsItem } from '@oca/web-shared';
import { Observable } from 'rxjs';
import { map, take } from 'rxjs/operators';
import { Loadable } from '../../../shared/loadable/loadable';
import { GetGlobalConfigAction } from '../../../shared/shared.actions';
import { isShopUser } from '../../../shared/shared.state';
import { ServiceNewsGroup } from '../../news';
import { CopyNewsItemAction, DeleteNewsItemAction, GetNewsListAction } from '../../news.actions';
import {
  getNewsCursor,
  getNewsItemListStatus,
  getNewsItems,
  getNewsOptions,
  hasMoreNews,
  initialNewsState,
  NewsState,
} from '../../news.state';

@Component({
  selector: 'oca-news-list-page',
  templateUrl: './news-list-page.component.html',
  changeDetection: ChangeDetectionStrategy.OnPush,
  encapsulation: ViewEncapsulation.None,
})
export class NewsListPageComponent implements OnInit {
  newsList$: Observable<NewsItem[]>;
  hasMore$: Observable<boolean>;
  listStatus$: Observable<Loadable>;
  newsGroups$: Observable<ServiceNewsGroup[]>;
  isShowUser$: Observable<boolean>;

  constructor(private store: Store<NewsState>) {
  }

  ngOnInit() {
    this.store.dispatch(new GetGlobalConfigAction());
    this.newsList$ = this.store.pipe(select(getNewsItems));
    this.hasMore$ = this.store.pipe(select(hasMoreNews));
    this.listStatus$ = this.store.pipe(select(getNewsItemListStatus));
    this.isShowUser$ = this.store.pipe(select(isShopUser));
    this.listStatus$.pipe(take(1)).subscribe(status => {
      if (status === initialNewsState.listStatus) {
        this.store.dispatch(new GetNewsListAction({ cursor: null }));
      }
    });
    this.newsGroups$ = this.store.pipe(select(getNewsOptions), map(o => o?.groups ?? []));
  }

  onLoadMore() {
    this.store.pipe(select(getNewsCursor), take(1)).subscribe(cursor => this.store.dispatch(new GetNewsListAction({ cursor })));
  }

  onDeleteItem(item: NewsItem) {
    this.store.dispatch(new DeleteNewsItemAction(item));
  }

  onCopyItem(item: NewsItem) {
    this.store.dispatch(new CopyNewsItemAction(item));
  }
}
