import { ChangeDetectionStrategy, Component, OnDestroy, OnInit, ViewEncapsulation } from '@angular/core';
import { Store } from '@ngrx/store';
import { Observable, Subscription } from 'rxjs';
import { first } from 'rxjs/operators';
import { ApiRequestStatus } from '../../../../framework/client/rpc';
import { SearchAppsAction } from '../../actions';
import * as states from '../../console.state';
import { AppSearchParameters, AppSearchResult } from '../../interfaces';
import { ConsoleState } from '../../reducers';

@Component({
  encapsulation: ViewEncapsulation.None,
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <rcc-app-list [apps]="apps$ | async"
                  [searchParams]="searchParams$ | async"
                  [appsStatus]="appsStatus$ | async"
                  (onSearch)="search($event)"></rcc-app-list>`,
})
export class AppListPageComponent implements OnInit, OnDestroy {
  apps$: Observable<AppSearchResult[]>;
  appsStatus$: Observable<ApiRequestStatus>;
  searchParams$: Observable<AppSearchParameters>;

  private _appStatusSubscription: Subscription;

  constructor(private store: Store) {
  }

  ngOnInit() {
    this.apps$ = <Observable<AppSearchResult[]>>this.store.select(states.getApps);
    this.appsStatus$ = this.store.select(states.getAppsStatus);
    this.searchParams$ = this.store.select(states.getAppSearchParameters);
    this._appStatusSubscription = this.appsStatus$.pipe(first()).subscribe(status => {
      if (!status.success) {
        this.search({});
      }
    });
  }

  ngOnDestroy() {
    this._appStatusSubscription.unsubscribe();
  }

  search(params: AppSearchParameters) {
    this.store.dispatch(new SearchAppsAction(params));
  }
}
