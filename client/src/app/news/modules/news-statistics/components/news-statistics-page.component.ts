import { ChangeDetectionStrategy, Component, OnInit } from '@angular/core';
import { ActivatedRoute } from '@angular/router';
import { select, Store } from '@ngrx/store';
import { NewsItemTimeStatistics, NewsStats } from '@oca/web-shared';
import { Observable } from 'rxjs';
import { map, take } from 'rxjs/operators';
import { Loadable } from '../../../../shared/loadable/loadable';
import { filterNull } from '../../../../shared/util';
import { GetNewsItemTimeStatsAction } from '../../../news.actions';
import { areNewsItemTimeStatsLoading, getNewsItemStats, getNewsItemTimeStats, NewsState } from '../../../news.state';
import { PossibleMetrics } from './news-statistics-graphs/news-statistics-graphs.component';

@Component({
  selector: 'oca-news-statistics-page',
  templateUrl: './news-statistics-page.component.html',
  changeDetection: ChangeDetectionStrategy.OnPush,
  styles: [`.totals-list {
    display: block;
    margin: 16px;
  }`],
})
export class NewsStatisticsPageComponent implements OnInit {
  newsItemWithStats$: Observable<Loadable<NewsStats>>;
  timeStats$: Observable<NewsItemTimeStatistics | null>;
  timeStatsLoading$: Observable<boolean>;
  selectedMetric$: Observable<PossibleMetrics>;

  constructor(private store: Store<NewsState>,
              private route: ActivatedRoute) {
  }

  ngOnInit() {
    this.newsItemWithStats$ = this.store.pipe(select(getNewsItemStats));
    this.timeStats$ = this.store.pipe(select(getNewsItemTimeStats));
    this.timeStatsLoading$ = this.store.pipe(select(areNewsItemTimeStatsLoading));
    const metricChoices = ['reached', 'action'];
    this.selectedMetric$ = this.route.queryParams.pipe(map(params => {
      if (params.metric && metricChoices.includes(params.metric)) {
        return params.metric;
      }
      return 'reached';
    }));
    this.newsItemWithStats$.pipe(map(s => s.data), filterNull(), take(1)).subscribe(stats => {
      this.store.dispatch(new GetNewsItemTimeStatsAction({ id: stats.news_item.id }));
    });
  }

}
