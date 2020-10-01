import { ChangeDetectionStrategy, Component, OnInit } from '@angular/core';
import { select, Store } from '@ngrx/store';
import { Observable } from 'rxjs';
import { switchMap } from 'rxjs/operators';
import { ApiRequestStatus } from '../../../../../framework/client/rpc';
import { UpdateRogerthatAppAction } from '../../../actions';
import { CommunityService } from '../../../communities/community.service';
import { Community } from '../../../communities/community/communities';
import { getRogerthatApp, getRogerthatAppStatus } from '../../../console.state';
import { RogerthatApp } from '../../../interfaces';
import { filterNull } from '../../../ngrx';

@Component({
  selector: 'rcc-app-advanced-configuration',
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <rcc-app-advanced-configuration-form
      [app]="app$ | async"
      [communities]="communities$ | async"
      [status]="appStatus$ | async"
      (save)="save($event)">
    </rcc-app-advanced-configuration-form>`,
})
export class AppAdvancedConfigurationComponent implements OnInit {
  app$: Observable<RogerthatApp>;
  appStatus$: Observable<ApiRequestStatus>;
  communities$: Observable<Community[]>;

  constructor(private store: Store,
              private communityService: CommunityService) {
  }

  ngOnInit() {
    this.app$ = this.store.pipe(select(getRogerthatApp), filterNull());
    this.appStatus$ = this.store.pipe(select(getRogerthatAppStatus));
    // TODO this should use the app service I think so we don't have a dependency on the community module
    this.communities$ = this.app$.pipe(switchMap(app => this.communityService.getCommunities(app.country)));
  }

  save(app: RogerthatApp) {
    this.store.dispatch(new UpdateRogerthatAppAction(app));
  }
}
