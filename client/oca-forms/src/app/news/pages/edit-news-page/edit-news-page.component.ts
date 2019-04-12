import { ChangeDetectionStrategy, Component, OnInit } from '@angular/core';
import { ActivatedRoute } from '@angular/router';
import { select, Store } from '@ngrx/store';
import { Observable, of } from 'rxjs';
import { map, tap } from 'rxjs/operators';
import { Budget } from '../../../shared/billing/billing';
import { Loadable } from '../../../shared/loadable/loadable';
import { AppStatistics, ServiceIdentityInfo } from '../../../shared/rogerthat';
import { GetAppStatisticsAction, GetBudgetAction, GetMenuAction, GetServiceIdentityAction } from '../../../shared/shared.actions';
import { getAppStats, getBudget, getInfo, getServiceMenu } from '../../../shared/shared.state';
import { CreateNews, NewsOptions, NewsStats, SimpleApp, UINewsActionButton } from '../../interfaces';
import { CreateNewsItemAction, GetNewsItemAction, SetNewNewsItemAction, UpdateNewsItemAction } from '../../news.actions';
import { NewsService } from '../../news.service';
import {
  getCreateNewsItem,
  getNewNewsItem,
  getNewsCityApps,
  getNewsItem,
  getNewsOptions,
  getNewsStatus,
  NewsState,
} from '../../news.state';

@Component({
  selector: 'oca-edit-news-page',
  templateUrl: './edit-news-page.component.html',
  styleUrls: [ './edit-news-page.component.scss' ],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class EditNewsPageComponent implements OnInit {
  newsItem$: Observable<Loadable<CreateNews>>;
  options$: Observable<Loadable<NewsOptions>>;
  status$: Observable<Loadable>;
  apps$: Observable<Loadable<SimpleApp[]>>;
  appStats$: Observable<Loadable<AppStatistics[]>>;
  budget$: Observable<Loadable<Budget>>;
  serviceInfo$: Observable<Loadable<ServiceIdentityInfo>>;
  isPublished$: Observable<boolean>;
  actionButtons$: Observable<Loadable<UINewsActionButton[]>>;
  temporaryItem: CreateNews | null;
  date = new Date();
  newsId: number | null;

  constructor(private _store: Store<NewsState>,
              private _route: ActivatedRoute,
              private _newsService: NewsService) {
  }

  ngOnInit() {
    this.newsId = parseInt(this._route.snapshot.params.id, 10);
    if (this.newsId) {
      // Load existing item from server
      this._store.dispatch(new GetNewsItemAction({ id: this.newsId }));
      this.isPublished$ = this._store.pipe(
        select(getNewsItem),
        map(s => s.data && s.data.news_item.published || false),
      );
      this.newsItem$ = this._store.pipe(select(getCreateNewsItem), tap(item => this.temporaryItem = item.data));
    } else {
      // Set up a new item
      this._store.dispatch(new SetNewNewsItemAction());
      this.newsItem$ = this._store.pipe(select(getNewNewsItem));
      this.isPublished$ = of(false);
    }
    this.apps$ = this._store.pipe(select(getNewsCityApps));
    this.appStats$ = this._store.pipe(select(getAppStats));
    this.budget$ = this._store.pipe(select(getBudget));
    this.serviceInfo$ = this._store.pipe(select(getInfo));
    this.options$ = this._store.pipe(select(getNewsOptions));
    this.actionButtons$ = this._store.pipe(
      select(getServiceMenu),
      map(menu => this._newsService.getActionButtons(menu)));
    this.status$ = this._store.pipe(select(getNewsStatus));
    this._store.dispatch(new GetMenuAction());
    this._store.dispatch(new GetServiceIdentityAction());
    this._store.dispatch(new GetAppStatisticsAction());
    this._store.dispatch(new GetBudgetAction());
  }

  onSave(event: CreateNews) {
    if (this.newsId) {
      this._store.dispatch(new UpdateNewsItemAction({ id: this.newsId, item: event }));
    } else {
      this._store.dispatch(new CreateNewsItemAction(event));
    }
  }

  onChargeBudget() {
    window.parent.location.href = '#/shop';
  }

  onNewsItemChange(event: CreateNews) {
    this.temporaryItem = event;
    this.date = new Date();
  }
}
