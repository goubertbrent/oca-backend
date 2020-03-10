import { ChangeDetectionStrategy, Component, OnDestroy, OnInit } from '@angular/core';
import { select, Store } from '@ngrx/store';
import { TranslateService } from '@ngx-translate/core';
import { Observable, Subject } from 'rxjs';
import { map, takeUntil, withLatestFrom } from 'rxjs/operators';
import { BrandingSettings } from '../../../shared/interfaces/oca';
import { App, AppStatisticsMapping, ServiceIdentityInfo } from '../../../shared/interfaces/rogerthat';
import { Loadable } from '../../../shared/loadable/loadable';
import {
  GetAppsAction,
  GetAppStatisticsAction,
  GetBrandingSettingsAction,
  GetBudgetAction,
  GetInfoAction,
  GetMenuAction,
} from '../../../shared/shared.actions';
import {
  getApps,
  getAppStatistics,
  getBrandingSettings,
  getBudget,
  getServiceIdentityInfo,
  getServiceMenu,
} from '../../../shared/shared.state';
import { BUDGET_RATE } from '../../consts';
import { CreateNews, NewsOptions, NewsSettingsTag, NewsStats, UINewsActionButton } from '../../interfaces';
import { CreateNewsItemAction, UpdateNewsItemAction } from '../../news.actions';
import { NewsService } from '../../news.service';
import { getEditingNewsItem, getNewsItemStats, getNewsOptions, NewsState } from '../../news.state';

@Component({
  selector: 'oca-edit-news-page',
  templateUrl: './edit-news-page.component.html',
  styleUrls: [ './edit-news-page.component.scss' ],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class EditNewsPageComponent implements OnInit, OnDestroy {
  newsItem$: Observable<Loadable<CreateNews>>;
  newsStats$: Observable<Loadable<NewsStats>>;
  options$: Observable<Loadable<NewsOptions>>;
  actionButtons$: Observable<Loadable<UINewsActionButton[]>>;
  serviceInfo$: Observable<Loadable<ServiceIdentityInfo>>;
  apps$: Observable<Loadable<App[]>>;
  appStatistics$: Observable<AppStatisticsMapping>;
  brandingSettings$: Observable<BrandingSettings | null>;
  remainingBudget$: Observable<string>;

  private hasRegionalNewsData = false;
  private destroyed$ = new Subject();

  constructor(private store: Store<NewsState>,
              private newsService: NewsService,
              private translate: TranslateService) {
  }

  ngOnInit() {
    this.newsStats$ = this.store.pipe(select(getNewsItemStats));
    this.newsItem$ = this.store.pipe(select(getEditingNewsItem));
    this.options$ = this.store.pipe(select(getNewsOptions));
    this.serviceInfo$ = this.store.pipe(select(getServiceIdentityInfo));
    this.apps$ = this.store.pipe(select(getApps));
    this.appStatistics$ = this.store.pipe(select(getAppStatistics));
    this.brandingSettings$ = this.store.pipe(select(getBrandingSettings));
    this.remainingBudget$ = this.options$.pipe(
      withLatestFrom(this.store.pipe(select(getBudget))),
      map(([ options, budget ]) => {
        let views: string | number = 0;
        if (options.data && options.data.tags.includes(NewsSettingsTag.FREE_REGIONAL_NEWS)) {
          views = this.translate.instant('oca.unlimited');
        } else if (budget.data) {
          views = BUDGET_RATE * budget.data.balance;
        }
        return this.translate.instant('oca.x_views', { views });
      }));
    this.actionButtons$ = this.store.pipe(
      select(getServiceMenu),
      map((menu) => this.newsService.getActionButtons(menu)));

    this.store.dispatch(new GetMenuAction());
    this.store.dispatch(new GetInfoAction());
    this.store.dispatch(new GetBrandingSettingsAction());
    this.newsItem$.pipe(withLatestFrom(this.serviceInfo$), takeUntil(this.destroyed$)).subscribe(([ item, info ]) => {
      if (item.data && info.data) {
        if (item.data.app_ids.length > 1 || item.data.app_ids[ 0 ] !== info.data.default_app) {
          this.fetchRegionalNewsData();
        }
      }
    });
  }

  ngOnDestroy(): void {
    this.destroyed$.next();
    this.destroyed$.complete();
  }

  onSave(event: CreateNews) {
    if (event.id) {
      this.store.dispatch(new UpdateNewsItemAction({ id: event.id, item: event }));
    } else {
      this.store.dispatch(new CreateNewsItemAction(event));
    }
  }

  onRegionalNewsToggled(enabled: boolean) {
    if (enabled) {
      this.fetchRegionalNewsData();
    }
  }

  private fetchRegionalNewsData() {
    if (!this.hasRegionalNewsData) {
      this.store.dispatch(new GetAppsAction());
      this.store.dispatch(new GetAppStatisticsAction());
      this.store.dispatch(new GetBudgetAction());
      this.hasRegionalNewsData = true;
    }
  }
}
