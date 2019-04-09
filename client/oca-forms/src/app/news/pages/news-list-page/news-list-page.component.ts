import { ChangeDetectionStrategy, Component, OnInit } from '@angular/core';
import { select, Store } from '@ngrx/store';
import { Observable } from 'rxjs';
import { take } from 'rxjs/operators';
import { Loadable } from '../../../shared/loadable/loadable';
import { NewsBroadcastItem } from '../../interfaces';
import { DeleteNewsItemAction, GetNewsListAction } from '../../news.actions';
import { getNewsCursor, getNewsItemListStatus, getNewsItems, hasMoreNews, NewsState } from '../../news.state';

@Component({
  selector: 'oca-news-list-page',
  templateUrl: './news-list-page.component.html',
  styleUrls: [ './news-list-page.component.scss' ],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class NewsListPageComponent implements OnInit {
  newsList$: Observable<NewsBroadcastItem[]>;
  hasMore$: Observable<boolean>;
  listStatus$: Observable<Loadable>;

  constructor(private store: Store<NewsState>) {
  }

  ngOnInit() {
    this.store.dispatch(new GetNewsListAction({ cursor: null }));
    this.newsList$ = this.store.pipe(select(getNewsItems));
    this.hasMore$ = this.store.pipe(select(hasMoreNews));
    this.listStatus$ = this.store.pipe(select(getNewsItemListStatus));
  }

  onLoadMore() {
    this.store.pipe(select(getNewsCursor), take(1)).subscribe(cursor => this.store.dispatch(new GetNewsListAction({ cursor })));
  }

  onDeleteItem(item: NewsBroadcastItem) {
    this.store.dispatch(new DeleteNewsItemAction({ id: item.id }));
  }
}
