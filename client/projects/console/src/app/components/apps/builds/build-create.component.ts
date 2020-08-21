import { ChangeDetectionStrategy, Component, OnDestroy, OnInit } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { Store } from '@ngrx/store';
import { TranslateService } from '@ngx-translate/core';
import { Observable, Subscription } from 'rxjs';
import { first } from 'rxjs/operators';
import { DialogService } from '../../../../../framework/client/dialog';
import { filterNull } from '../../../ngrx';
import { ApiRequestStatus } from '../../../../../framework/client/rpc';
import * as actions from '../../../actions';
import { ClearBuildAction } from '../../../actions';
import * as states from '../../../console.state';
import { App, BUILD_TYPE_STRINGS, BuildType, CreateBuildPayload, GitStatus, TrackTypes } from '../../../interfaces';
import { ConsoleState } from '../../../reducers';

@Component({
  selector: 'rcc-build-create',
  changeDetection: ChangeDetectionStrategy.OnPush,
  templateUrl: 'build-create.component.html',
  styleUrls: ['build-create.component.css'],
})
export class BuildCreateComponent implements OnInit, OnDestroy {
  status$: Observable<ApiRequestStatus>;
  buildOptions: CreateBuildPayload;
  buildTypes: BuildType[] = [BuildType.ANDROID, BuildType.IOS];
  trackTypes = TrackTypes.TYPES;
  appId: string;
  private appIsDraft: boolean;
  private subscription: Subscription;
  private appChangedSub: Subscription;

  constructor(private store: Store,
              private route: ActivatedRoute,
              private router: Router,
              private dialogService: DialogService,
              private translate: TranslateService) {
  }

  ngOnInit() {
    this.store.dispatch(new ClearBuildAction());
    this.buildOptions = {
      type: this.buildTypes[ 0 ],
      release: false,
      debug: false,
      generate_screenshots: false,
      track: this.trackTypes[ 0 ],
      submit_for_review: true,
      branch: null,
    };
    this.appChangedSub = this.store.select(states.getApp).pipe(filterNull())
      .subscribe(this.appChanged.bind(this));
    this.status$ = this.store.select(states.getCreateBuildStatus);
    this.subscription = this.status$.pipe(first(s => s.success))
      .subscribe(() => this.router.navigate(['../'], { relativeTo: this.route }));
    this.appId = (<ActivatedRoute>this.route.parent).snapshot.params[ 'appId' ];
    this.store.dispatch(new actions.GetAppAction(this.appId));
  }

  ngOnDestroy() {
    this.subscription.unsubscribe();
    this.appChangedSub.unsubscribe();
  }

  isAndroid() {
    return this.buildOptions.type === BuildType.ANDROID;
  }

  releaseChanged() {
    if (this.buildOptions.release) {
      this.buildOptions = { ...this.buildOptions, debug: false, submit_for_review: true };
    } else {
      this.buildOptions = { ...this.buildOptions, generate_screenshots: false, submit_for_review: false };
    }
  }

  appChanged(app: App) {
    this.buildOptions = { ...this.buildOptions, track: app.playstore_track };
    this.appIsDraft = app.git_status === GitStatus.DRAFT;
  }

  createBuild() {
    this.store.dispatch(new actions.CreateBuildAction({ app_id: this.appId, data: { ...this.buildOptions } }));
  }

  getBuildTypeString(buildType: BuildType) {
    return BUILD_TYPE_STRINGS[ buildType ];
  }

  checkPendingChanges() {
    if (this.appIsDraft) {
      const options = {
        ok: this.translate.instant('rcc.ok'),
        cancel: this.translate.instant('rcc.cancel'),
        title: this.translate.instant('rcc.publish'),
        message: this.translate.instant('rcc.publish_automatically_before_build'),
      };
      const sub = this.dialogService.openConfirm(options).afterClosed()
        .subscribe((confirmed: boolean) => {
          if (confirmed) {
            this.createBuild();
          }
          sub.unsubscribe();
        });
    } else {
      this.createBuild();
    }
  }
}
