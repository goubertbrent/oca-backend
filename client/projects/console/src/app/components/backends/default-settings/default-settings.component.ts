import { ChangeDetectionStrategy, Component, OnInit } from '@angular/core';
import { Store } from '@ngrx/store';
import { GetBackendRogerthatAppsAction } from '../../../actions/backends.actions';

@Component({
  selector: 'rcc-backend-default-settings',
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: '<router-outlet></router-outlet>',
})
export class BackendDefaultSettingsComponent implements OnInit {

  constructor(private store: Store) {
  }

  ngOnInit() {
    this.store.dispatch(new GetBackendRogerthatAppsAction());
  }
}
