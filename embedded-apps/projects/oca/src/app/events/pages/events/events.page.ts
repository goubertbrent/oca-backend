import { ChangeDetectionStrategy, Component, OnDestroy, OnInit, ViewChild } from '@angular/core';
import { IonInfiniteScroll } from '@ionic/angular';
import { select, Store } from '@ngrx/store';
import {
  getNewsStreamItems,
  GetNewsStreamItemsAction,
  getNewsStreamItemsList,
  isNewsStreamItemsLoading,
  NewsStreamItem,
  shouldShowNews,
} from '@oca/rogerthat';
import { CallStateType } from '@oca/shared';
import { OpenParams } from 'rogerthat-plugin';
import { Observable, of, Subject } from 'rxjs';
import { debounceTime, map, take, takeUntil, tap } from 'rxjs/operators';
import { EventAnnouncementList, EventFilterPeriod, EventListItem, GetEventsParams } from '../../events';
import { GetAnnouncementsAction, GetEventsAction, GetMoreEventsAction } from '../../events.actions';
import { EventsService } from '../../events.service';
import { eventsLoading, EventsState, getEventAnnouncements, getEvents, getEventsFilter, hasMoreEvents } from '../../events.state';

@Component({
  selector: 'app-events',
  templateUrl: './events.page.html',
  styleUrls: ['./events.page.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class EventsPage implements OnInit, OnDestroy {
  @ViewChild(IonInfiniteScroll, { static: true }) infiniteScroll: IonInfiniteScroll;
  readonly fakeItems = [1, 2, 3, 4, 5, 6];
  announcementList$: Observable<EventAnnouncementList | null>;
  newsStreamItems$: Observable<NewsStreamItem[]>;
  shouldShowNews$: Observable<boolean>;
  newsLoading$: Observable<boolean>;
  eventsLoading$: Observable<boolean>;
  openNewsParams$: Observable<OpenParams | null>;
  eventsFilter$: Observable<GetEventsParams>;
  events$: Observable<EventListItem[]>;
  delayedSearch$ = new Subject<GetEventsParams>();

  private readonly destroyed$ = new Subject();
  private readonly service: string | null = null;

  constructor(private store: Store<EventsState>,
              private eventsService: EventsService) {
    if (rogerthat.service.account !== rogerthat.system.mainService) {
      this.service = rogerthat.service.account;
    }
  }

  ngOnInit() {
    this.store.dispatch(new GetAnnouncementsAction());
    this.announcementList$ = this.store.pipe(select(getEventAnnouncements));

    const period = this.service ? EventFilterPeriod.RANGE : EventFilterPeriod.NEXT_7;
    const { startDate, endDate } = this.eventsService.getStartEndDate(period);
    this.doSearch({ startDate: startDate.toISOString(), endDate: endDate.toISOString(), period });
    this.events$ = this.store.pipe(
      select(getEvents),
      map(list => this.eventsService.convertEventList(list)),
      tap(() => this.infiniteScroll.complete()),
    );
    this.store.pipe(select(hasMoreEvents), takeUntil(this.destroyed$)).subscribe(hasMore => {
      this.infiniteScroll.disabled = !hasMore;
    });
    this.eventsLoading$ = this.store.pipe(select(eventsLoading));
    this.newsStreamItems$ = this.store.pipe(select(getNewsStreamItemsList));
    this.newsLoading$ = this.store.pipe(select(isNewsStreamItemsLoading));
    this.eventsFilter$ = this.store.pipe(select(getEventsFilter));
    this.openNewsParams$ = this.store.pipe(select(getNewsStreamItems), map(result => result.state === CallStateType.SUCCESS ? ({
      action: 'news_stream_group',
      params: { group_id: result.result.group_id, service: this.service },
    }) : null));
    if (rogerthat.news && rogerthat.news.getNewsGroup) {
      this.shouldShowNews$ = this.store.pipe(select(shouldShowNews));
      this.store.dispatch(new GetNewsStreamItemsAction({
        cursor: null,
        news_ids: [],
        filter: { group_id: null, search_string: null, service_identity_email: this.service, group_type: 'events' },
      }));
    } else {
      this.shouldShowNews$ = of(false);
    }
    // Wait at least 600ms before searching (to not spam the server with requests when typing)
    this.delayedSearch$.asObservable().pipe(debounceTime(600), takeUntil(this.destroyed$)).subscribe(params => this.doSearch(params));
  }

  ngOnDestroy(): void {
    this.destroyed$.next();
    this.destroyed$.complete();
    this.delayedSearch$.unsubscribe();
  }

  trackById(index: number, event: EventListItem) {
    return event.id;
  }

  loadMore() {
    this.eventsFilter$.pipe(take(1)).subscribe(filter => {
      this.store.dispatch(new GetMoreEventsAction(filter));
    });
  }

  open(openParams: OpenParams) {
    rogerthat.util.open(openParams);
  }

  onNewsItemClicked($event: NewsStreamItem) {
    this.openNewsParams$.pipe(take(1)).subscribe(params => {
      if (params) {
        const extra = this.service ? { filter: 'service', key: this.service, name: rogerthat.service.name } : {};
        rogerthat.util.open({ ...params, params: { ...params.params, id: $event.id, ...extra } });
      }
    });
  }

  doSearch($event: GetEventsParams) {
    this.store.dispatch(new GetEventsAction($event));
  }
}
