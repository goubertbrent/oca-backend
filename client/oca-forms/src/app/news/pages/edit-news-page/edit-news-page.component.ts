import { ChangeDetectionStrategy, Component, OnInit } from '@angular/core';
import { ActivatedRoute } from '@angular/router';
import { select, Store } from '@ngrx/store';
import { Observable } from 'rxjs';
import { map } from 'rxjs/operators';
import { Loadable } from '../../../shared/loadable/loadable';
import { GetMenuAction } from '../../../shared/shared.actions';
import { getServiceMenu } from '../../../shared/shared.state';
import { CreateNews, NewsOptions, NewsStats, UINewsActionButton } from '../../interfaces';
import { GetNewsItemAction } from '../../news.actions';
import { NewsService } from '../../news.service';
import { getCreateNewsItem, getNewsItem, getNewsOptions, NewsState } from '../../news.state';

@Component({
  selector: 'oca-edit-news-page',
  templateUrl: './edit-news-page.component.html',
  styleUrls: [ './edit-news-page.component.scss' ],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class EditNewsPageComponent implements OnInit {
  newsItem$: Observable<Loadable<CreateNews>>;
  newsStats$: Observable<Loadable<NewsStats>>;
  options$: Observable<Loadable<NewsOptions>>;
  actionButtons$: Observable<Loadable<UINewsActionButton[]>>;

  constructor(private _store: Store<NewsState>,
              private _route: ActivatedRoute,
              private _newsService: NewsService) {
  }

  ngOnInit() {
    const id: number = parseInt(this._route.snapshot.params.id, 10);
    this._store.dispatch(new GetNewsItemAction({ id }));
    this.newsStats$ = this._store.pipe(select(getNewsItem));
    this.newsItem$ = this._store.pipe(select(getCreateNewsItem));
    this.options$ = this._store.pipe(select(getNewsOptions));
    this.actionButtons$ = this._store.pipe(
      select(getServiceMenu),
      map(menu => this._newsService.getActionButtons(menu)));
    this._store.dispatch(new GetMenuAction());
  }

  onSave(event: CreateNews) {

  }
}
