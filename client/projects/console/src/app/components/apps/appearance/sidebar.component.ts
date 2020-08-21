import { ChangeDetectionStrategy, Component, OnInit } from '@angular/core';
import { select, Store } from '@ngrx/store';
import { Observable } from 'rxjs';
import { map } from 'rxjs/operators';
import { filterNull } from '../../../ngrx';
import { ApiRequestStatus } from '../../../../../framework/client/rpc';
import { GetAppSidebarAction, GetBuildSettingsAction, UpdateAppSidebarAction } from '../../../actions';
import { getApp, getAppSidebar, getAppSidebarStatus, getBuildSettings } from '../../../console.state';
import { HOMESCREEN_STYLES, HomescreenStyle } from '../../../constants';
import { AppSidebar, BuildSettings } from '../../../interfaces';

@Component({
  selector: 'rcc-appearance-sidebar',
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <div class="default-component-margin">
      <rcc-app-sidebar-form [sidebar]="sidebar$ | async"
                            [homescreenStyles]="homescreenStyles$ | async"
                            [status]="status$ | async"
                            [buildSettings]="buildSettings$ | async"
                            (save)="save($event)"></rcc-app-sidebar-form>
    </div>`,
})
export class AppearanceSidebarComponent implements OnInit {
  sidebar$: Observable<AppSidebar>;
  status$: Observable<ApiRequestStatus>;
  buildSettings$: Observable<BuildSettings>;
  homescreenStyles$: Observable<HomescreenStyle[]>;

  constructor(private store: Store) {
  }

  ngOnInit() {
    this.store.dispatch(new GetAppSidebarAction());
    this.store.dispatch(new GetBuildSettingsAction());
    this.sidebar$ = this.store.pipe(select(getAppSidebar), filterNull());
    this.status$ = this.store.pipe(select(getAppSidebarStatus));
    this.buildSettings$ = this.store.pipe(select(getBuildSettings), filterNull());
    this.homescreenStyles$ = this.store.pipe(
      select(getApp),
      filterNull(),
      map(app => app.main_service ? HOMESCREEN_STYLES : HOMESCREEN_STYLES.filter(style => style !== HomescreenStyle.BRANDING)),
    );
  }

  save(sidebar: AppSidebar) {
    this.store.dispatch(new UpdateAppSidebarAction(sidebar));
  }
}
