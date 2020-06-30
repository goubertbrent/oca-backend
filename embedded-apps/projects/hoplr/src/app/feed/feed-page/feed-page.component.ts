import { ChangeDetectionStrategy, Component, OnDestroy, OnInit, ViewChild } from '@angular/core';
import { AlertController, IonInfiniteScroll } from '@ionic/angular';
import { select, Store } from '@ngrx/store';
import { TranslateService } from '@ngx-translate/core';
import { Observable, Subject } from 'rxjs';
import { map, take, takeUntil } from 'rxjs/operators';
import { GetUserInformationResult, HoplrFeed } from '../../hoplr';
import { GetFeedAction, LogoutAction } from '../../hoplr.actions';
import { getFeed, getFeedPage, getNeighbourhood, getUserInformation, HoplrAppState, isFeedLoading } from '../../state';

@Component({
  selector: 'hoplr-feed-page',
  templateUrl: './feed-page.component.html',
  styleUrls: ['./feed-page.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class FeedPageComponent implements OnInit, OnDestroy {
  @ViewChild(IonInfiniteScroll, { static: true }) infiniteScroll: IonInfiniteScroll;
  neighbourhoodName$: Observable<string>;
  userInfo$: Observable<GetUserInformationResult | null>;
  feed$: Observable<HoplrFeed | null>;
  loading$: Observable<boolean>;
  hasMore$: Observable<boolean>;
  destroyed$ = new Subject();

  constructor(private store: Store<HoplrAppState>,
              private translate: TranslateService,
              private alertController: AlertController) {
  }

  ngOnInit() {
    this.store.dispatch(new GetFeedAction({}));
    this.neighbourhoodName$ = this.store.pipe(select(getNeighbourhood), map(n => n?.Title ?? 'Hoplr'));
    this.userInfo$ = this.store.pipe(select(getUserInformation));
    this.feed$ = this.store.pipe(select(getFeed));
    this.hasMore$ = this.feed$.pipe(map(feed => feed?.more ?? true));
    this.loading$ = this.store.pipe(select(isFeedLoading));
    this.loading$.pipe(takeUntil(this.destroyed$)).subscribe(loading => {
      if (!loading && !this.infiniteScroll.disabled) {
        this.infiniteScroll.complete();
      }
    });
  }

  ngOnDestroy() {
    this.destroyed$.next();
    this.destroyed$.complete();
  }

  loadMore() {
    this.store.pipe(select(getFeedPage), take(1)).subscribe(page => {
      this.store.dispatch(new GetFeedAction({ page: page + 1 }));
    });
  }

  async confirmLogout() {
    const dialog = await this.alertController.create({
      header: this.translate.instant('app.hoplr.logout_confirmation'),
      message: this.translate.instant('app.hoplr.confirm_logout'),
      buttons: [
        {
          role: 'cancel',
          text: this.translate.instant('app.hoplr.cancel'),
        },
        {
          role: 'confirm',
          text: this.translate.instant('app.hoplr.log_out'),
        },
      ],
    });
    await dialog.present();
    const result = await dialog.onDidDismiss();
    if (result.role === 'confirm') {
      this.store.dispatch(new LogoutAction());
    }
  }
}
