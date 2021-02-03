import { Clipboard } from '@angular/cdk/clipboard';
import { ChangeDetectionStrategy, Component, OnDestroy, OnInit } from '@angular/core';
import { MatSnackBar } from '@angular/material/snack-bar';
import { DomSanitizer, SafeResourceUrl } from '@angular/platform-browser';
import { ActivatedRoute } from '@angular/router';
import { select, Store } from '@ngrx/store';
import { TranslateService } from '@ngx-translate/core';
import { MediaType, NewsItem } from '@oca/web-shared';
import { Observable, Subject } from 'rxjs';
import { map, takeUntil } from 'rxjs/operators';
import { RootState } from '../../app.reducer';
import { maybeDispatch } from '../../initial-state';
import { GetNewsItem, SaveNewsItemStatistic } from '../news.actions';
import { getCurrentNewsItem, getCurrentNewsItemError, isCurrentNewsItemLoading } from '../news.selectors';
import { NewsService, NewsStatisticsActionType } from '../news.service';

@Component({
  selector: 'web-news-item-page',
  templateUrl: './news-item-page.component.html',
  styleUrls: ['./news-item-page.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class NewsItemPageComponent implements OnInit, OnDestroy {
  newsId: number;
  newsItem$: Observable<NewsItem | null>;
  error$: Observable<string | null>;
  loading$: Observable<boolean>;
  newsItemError$: Observable<string | null>;
  MediaType = MediaType;
  youtubeUrl$: Observable<SafeResourceUrl | undefined>;

  private destroyed$ = new Subject();

  constructor(private route: ActivatedRoute,
              private domSanitizer: DomSanitizer,
              private snackbar: MatSnackBar,
              private translate: TranslateService,
              private clipboard: Clipboard,
              private newsService: NewsService,
              private store: Store<RootState>) {
  }

  ngOnInit(): void {
    this.loading$ = this.store.pipe(select(isCurrentNewsItemLoading));
    this.newsItem$ = this.store.pipe(select(getCurrentNewsItem));
    this.newsItemError$ = this.store.pipe(select(getCurrentNewsItemError));
    this.youtubeUrl$ = this.newsItem$.pipe(
      map(item => item?.media?.type === MediaType.VIDEO_YOUTUBE &&
        this.domSanitizer.bypassSecurityTrustResourceUrl(`https://www.youtube.com/embed/${item.media.content}`)),
    );
    this.route.params.pipe(takeUntil(this.destroyed$)).subscribe(params => {
      const newsId = parseInt(params.newsId, 10);
      this.newsId = newsId;
      maybeDispatch(this.store, getCurrentNewsItem, item => item?.id === newsId,
        new GetNewsItem({ id: newsId, appUrlName: params.cityUrlName }));
      this.newsService.saveNewsStatistic(params.cityUrlName, newsId, NewsStatisticsActionType.REACH).subscribe();
    });
  }

  ngOnDestroy() {
    this.destroyed$.next();
    this.destroyed$.complete();
  }

  share(newsItem: NewsItem) {
    const url = newsItem.share_url;
    if (!url) {
      return;
    }
    if (navigator.hasOwnProperty('share')) {
      // @ts-ignore
      navigator.share({
        title: this.translate.instant('web.our_city_app'),
        text: newsItem.title,
        url,
      }).catch(() => this.copyToClipboard(url));
    } else {
      this.copyToClipboard(url);
    }
    this.saveStatistic(NewsStatisticsActionType.SHARE);
  }

  private saveStatistic(action: NewsStatisticsActionType) {
    const { newsId, cityUrlName } = this.route.snapshot.params;
    this.store.dispatch(new SaveNewsItemStatistic({appUrlName: cityUrlName, id: parseInt(newsId, 10), action}));
  }

  private copyToClipboard(url: string) {
    const success = this.clipboard.copy(url);
    if (success) {
      this.snackbar.open(this.translate.instant('web.link_copied_to_clipboard'), undefined, { duration: 5000 });
    }
  }

  actionClicked() {
    this.saveStatistic(NewsStatisticsActionType.ACTION);
  }
}
