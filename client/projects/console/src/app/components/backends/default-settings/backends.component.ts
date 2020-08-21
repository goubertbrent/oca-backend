import { ChangeDetectionStrategy, Component, OnInit } from '@angular/core';
import { Store } from '@ngrx/store';
import { Observable } from 'rxjs';
import { ApiRequestStatus } from '../../../../../framework/client/rpc';
import { GetBackendBrandingsAction, RemoveBackendBrandingAction } from '../../../actions';
import { getBackendBrandings, getBackendBrandingsStatus } from '../../../console.state';
import { DefaultBranding } from '../../../interfaces';
import { ConsoleState } from '../../../reducers';

@Component({
  selector: 'rcc-backend-brandings',
  changeDetection: ChangeDetectionStrategy.OnPush,
  templateUrl: 'brandings.component.html',
})
export class BackendBrandingsComponent implements OnInit {
  brandings$: Observable<DefaultBranding[]>;
  status$: Observable<ApiRequestStatus>;

  constructor(private store: Store) {
  }

  ngOnInit() {
    this.store.dispatch(new GetBackendBrandingsAction());
    this.brandings$ = this.store.select(getBackendBrandings);
    this.status$ = this.store.select(getBackendBrandingsStatus);
  }

  removeBranding(branding: DefaultBranding) {
    this.store.dispatch(new RemoveBackendBrandingAction(branding));
  }
}
