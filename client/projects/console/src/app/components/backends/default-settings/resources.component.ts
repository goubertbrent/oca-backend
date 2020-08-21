import { ChangeDetectionStrategy, Component, OnInit } from '@angular/core';
import { Store } from '@ngrx/store';
import { Observable } from 'rxjs';
import { ApiRequestStatus } from '../../../../../framework/client/rpc';
import { GetBackendAppAssetsAction, RemoveBackendAppAssetAction } from '../../../actions';
import { getBackendAppAssets, getBackendAppAssetsStatus } from '../../../console.state';
import { AppAsset } from '../../../interfaces';

@Component({
  selector: 'rcc-backend-resources',
  changeDetection: ChangeDetectionStrategy.OnPush,
  templateUrl: 'resources.component.html',
})
export class BackendResourcesComponent implements OnInit {
  appAssets$: Observable<AppAsset[]>;
  status$: Observable<ApiRequestStatus>;

  constructor(private store: Store) {
  }

  ngOnInit() {
    this.store.dispatch(new GetBackendAppAssetsAction());
    this.appAssets$ = this.store.select(getBackendAppAssets);
    this.status$ = this.store.select(getBackendAppAssetsStatus);
  }

  removeAsset(asset: AppAsset) {
    this.store.dispatch(new RemoveBackendAppAssetAction(asset));
  }
}
