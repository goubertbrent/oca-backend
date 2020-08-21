import { ChangeDetectionStrategy, Component, OnInit } from '@angular/core';
import { ActivatedRoute } from '@angular/router';
import { select, Store } from '@ngrx/store';
import { Observable } from 'rxjs';
import * as actions from '../../../actions/index';
import * as states from '../../../console.state';
import { Build, BUILD_STATUS_STRINGS, BUILD_TYPE_STRINGS, BuildStatus, BuildType } from '../../../interfaces';
import { ConsoleConfig } from '../../../services';

@Component({
  selector: 'rcc-build-list',
  changeDetection: ChangeDetectionStrategy.OnPush,
  templateUrl: 'build-list.component.html',
})
export class BuildListComponent implements OnInit {
  builds$: Observable<Build[]>;
  statusColors = {
    [ BuildStatus.CREATED ]: 'accent',
    [ BuildStatus.RUNNING ]: 'accent',
    [ BuildStatus.SUCCESS ]: 'primary',
    [ BuildStatus.FAILURE ]: 'warn',
    [ BuildStatus.ABORTED ]: '',
  };

  constructor(private store: Store,
              private route: ActivatedRoute) {
  }

  ngOnInit() {
    this.store.dispatch(new actions.GetBuildsAction((<ActivatedRoute>this.route.parent).snapshot.params[ 'appId' ]));
    this.builds$ = this.store.pipe(select(states.getBuilds));
  }

  getStatusColor(status: BuildStatus): string {
    return status ? this.statusColors[ status ] : '';
  }

  getDownloadUrl(build: Build) {
    if (build.type === BuildType.ANDROID) {
      return build.download_url;
    } else if (build.type === BuildType.IOS) {
      return `${ConsoleConfig.BUILDSERVER_URL}/builds/${build.id}/install`;
    }
    return null;
  }

  getBuildTypeString(buildType: BuildType) {
    return BUILD_TYPE_STRINGS[ buildType ];
  }

  getBuildStatusString(buildType: BuildStatus) {
    return BUILD_STATUS_STRINGS[ buildType ];
  }

  isAndroid(build: Build) {
    return build.type === BuildType.ANDROID;
  }

  trackBuilds(index: number, value: Build) {
    return value.id;
  }
}
