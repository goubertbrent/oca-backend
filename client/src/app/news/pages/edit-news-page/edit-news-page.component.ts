import { ChangeDetectionStrategy, Component, OnDestroy, OnInit } from '@angular/core';
import { Router } from '@angular/router';
import { select, Store } from '@ngrx/store';
import { TranslateService } from '@ngx-translate/core';
import { ErrorService } from '@oca/web-shared';
import { Observable, Subject } from 'rxjs';
import { distinctUntilChanged, map, takeUntil, withLatestFrom } from 'rxjs/operators';
import { BrandingSettings } from '../../../shared/interfaces/oca';
import { Loadable } from '../../../shared/loadable/loadable';
import { GetBrandingSettingsAction, GetBudgetAction } from '../../../shared/shared.actions';
import { getBrandingSettings, getBudget } from '../../../shared/shared.state';
import { filterNull } from '../../../shared/util';
import { BUDGET_RATE } from '../../consts';
import { CreateNews, NewsCommunity, NewsOptions, NewsSettingsTag, NewsStats } from '../../news';
import { CreateNewsItemAction, GetCommunities, GetNewsOptionsAction, UpdateNewsItemAction } from '../../news.actions';
import { NewsService } from '../../news.service';
import { getEditingNewsItem, getNewsCommunities, getNewsItemStats, getNewsOptions, getNewsOptionsError, NewsState } from '../../news.state';

@Component({
  selector: 'oca-edit-news-page',
  templateUrl: './edit-news-page.component.html',
  styleUrls: [ './edit-news-page.component.scss' ],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class EditNewsPageComponent implements OnInit, OnDestroy {
  newsItem$: Observable<Loadable<CreateNews>>;
  newsStats$: Observable<Loadable<NewsStats>>;
  options$: Observable<NewsOptions | null>;
  communities$: Observable<NewsCommunity[]>;
  brandingSettings$: Observable<BrandingSettings | null>;
  remainingBudget$: Observable<string>;

  private hasRegionalNewsData = false;
  private destroyed$ = new Subject();

  constructor(private store: Store<NewsState>,
              private newsService: NewsService,
              private errorService: ErrorService,
              private router: Router,
              private translate: TranslateService) {
  }

  ngOnInit() {
    // Ensure all possible action buttons are present by always reloading this information
    this.store.dispatch(new GetNewsOptionsAction());
    this.options$ = this.store.pipe(select(getNewsOptions));
    this.newsStats$ = this.store.pipe(select(getNewsItemStats));
    this.newsItem$ = this.store.pipe(select(getEditingNewsItem));
    this.communities$ = this.store.pipe(select(getNewsCommunities));
    this.brandingSettings$ = this.store.pipe(select(getBrandingSettings));
    this.store.pipe(select(getNewsOptionsError), filterNull(), takeUntil(this.destroyed$), distinctUntilChanged()).subscribe(error => {
      this.errorService.showErrorDialog(error).afterClosed().subscribe(() => {
        this.router.navigate(['/news']);
      });
    });
    this.remainingBudget$ = this.options$.pipe(
      withLatestFrom(this.store.pipe(select(getBudget))),
      map(([options, budget]) => {
        let views: string | number = 0;
        if (options?.tags.includes(NewsSettingsTag.FREE_REGIONAL_NEWS)) {
          views = this.translate.instant('oca.unlimited');
        } else if (budget.data) {
          views = BUDGET_RATE * budget.data.balance;
        }
        return this.translate.instant('oca.x_views', { views });
      }));
    this.store.dispatch(new GetBrandingSettingsAction());
    this.newsItem$.pipe(withLatestFrom(this.options$), takeUntil(this.destroyed$)).subscribe(([item, options]) => {
      if (item.data && options) {
        if (item.data.community_ids.length > 1 || item.data.community_ids[ 0 ] !== options.community_id) {
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
      this.store.dispatch(new GetCommunities());
      this.store.dispatch(new GetBudgetAction());
      this.hasRegionalNewsData = true;
    }
  }
}
