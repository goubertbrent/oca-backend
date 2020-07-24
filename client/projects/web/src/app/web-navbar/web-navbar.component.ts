import { ChangeDetectionStrategy, Component, OnInit } from '@angular/core';
import { select, Store } from '@ngrx/store';
import { PublicAppInfo } from '@oca/web-shared';
import { Observable } from 'rxjs';
import { AppState } from '../app.reducer';
import { getAppInfo } from '../app.selectors';

@Component({
  selector: 'web-navbar',
  templateUrl: './web-navbar.component.html',
  styleUrls: ['./web-navbar.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class WebNavbarComponent implements OnInit {
  appInfo$: Observable<PublicAppInfo | null>;

  constructor(private store: Store<AppState>) {
  }

  ngOnInit() {
    this.appInfo$ = this.store.pipe(select(getAppInfo));
  }

}
