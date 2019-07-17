import { ChangeDetectionStrategy, Component, OnInit, ViewEncapsulation } from '@angular/core';
import { select, Store } from '@ngrx/store';
import { Observable } from 'rxjs';
import { map } from 'rxjs/operators';
import { NonNullLoadable } from '../../../shared/loadable/loadable';
import { deepCopy } from '../../../shared/util/misc';
import { GetIntegrationsAction, UpdateIntegrationAction } from '../../forms.actions';
import { FormsState, getIntegrations } from '../../forms.state';
import { FormIntegrationConfiguration } from '../../interfaces/integrations';

@Component({
  selector: 'oca-forms-settings-page',
  templateUrl: './forms-settings-page.component.html',
  encapsulation: ViewEncapsulation.None,
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class FormsSettingsPageComponent implements OnInit {
  integrations$: Observable<NonNullLoadable<FormIntegrationConfiguration[]>>;
  configurations$: Observable<FormIntegrationConfiguration[]>;

  constructor(private store: Store<FormsState>) {
  }

  ngOnInit() {
    this.integrations$ = this.store.pipe(select(getIntegrations), map(i => deepCopy(i)));
    this.configurations$ = this.integrations$.pipe(map(i => i.data));
    this.store.dispatch(new GetIntegrationsAction());
  }

  onUpdateConfiguration(config: FormIntegrationConfiguration) {
    this.store.dispatch(new UpdateIntegrationAction(config));
  }

}
