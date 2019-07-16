import { ChangeDetectionStrategy, Component, OnInit, ViewEncapsulation } from '@angular/core';
import { ActivatedRoute } from '@angular/router';
import { select, Store } from '@ngrx/store';
import { Observable } from 'rxjs';
import { map } from 'rxjs/operators';
import { Loadable } from '../../../../shared/loadable/loadable';
import { NewsStats } from '../../../interfaces';
import { getNewsItemStats, NewsState } from '../../../news.state';
import { PossibleMetrics } from './news-statistics-graphs/news-statistics-graphs.component';

@Component({
  selector: 'oca-news-statistics-page',
  templateUrl: './news-statistics-page.component.html',
  changeDetection: ChangeDetectionStrategy.OnPush,
  encapsulation: ViewEncapsulation.None,
})
export class NewsStatisticsPageComponent implements OnInit {
  newsItemStats$: Observable<Loadable<NewsStats>>;
  selectedMetric$: Observable<PossibleMetrics>;

  constructor(private store: Store<NewsState>,
              private route: ActivatedRoute) {
  }

  ngOnInit() {
    this.newsItemStats$ = this.store.pipe(select(getNewsItemStats));
    const metricChoices = [ 'reached', 'rogered', 'action', 'followed' ];
    this.selectedMetric$ = this.route.queryParams.pipe(map(params => {
      if (params.metric && metricChoices.includes(params.metric)) {
        return params.metric;
      }
      return 'reached';
    }));
  }

}
