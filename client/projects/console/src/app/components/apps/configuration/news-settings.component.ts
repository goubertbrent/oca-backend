import { ChangeDetectionStrategy, Component, OnInit } from '@angular/core';
import { Store } from '@ngrx/store';
import { Observable } from 'rxjs';
import { filterNull } from '../../../ngrx';
import { ApiRequestStatus } from '../../../../../framework/client/rpc';
import { GetNewsSettingsAction } from '../../../actions';
import { getNewsSettings, getNewsSettingsStatus } from '../../../console.state';
import { NewsSettings } from '../../../interfaces';

@Component({
  selector: 'rcc-news-settings',
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <rcc-news-settings-form [newsSettings]="newsSettings$ | async"
                            [status]="status$ | async"
                            [updateStatus]="updateStatus$ | async"></rcc-news-settings-form>`,
})
export class NewsSettingsComponent implements OnInit {
  newsSettings$: Observable<NewsSettings>;
  status$: Observable<ApiRequestStatus>;
  updateStatus$: Observable<ApiRequestStatus>;

  constructor(private store: Store) {
  }

  ngOnInit() {
    this.newsSettings$ = this.store.select(getNewsSettings).pipe(filterNull());
    this.status$ = this.store.select(getNewsSettingsStatus);
    this.store.dispatch(new GetNewsSettingsAction());
  }
}
