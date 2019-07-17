import {
  ChangeDetectionStrategy,
  Component,
  EventEmitter,
  Input,
  OnChanges,
  Output,
  SimpleChanges,
  ViewEncapsulation,
} from '@angular/core';
import { updateItem } from '../../../shared/util/redux';
import { FormSection } from '../../interfaces/forms';
import {
  FormIntegration,
  FormIntegrationGreenValley,
  FormIntegrationProvider,
  GVIntegrationFormConfig,
} from '../../interfaces/integrations';

interface ProviderMapping {
  [ FormIntegrationProvider.GREEN_VALLEY ]: {
    enabled: boolean,
    integration: FormIntegrationGreenValley | null
  };
}

@Component({
  selector: 'oca-form-integrations',
  templateUrl: './form-integrations.component.html',
  encapsulation: ViewEncapsulation.None,
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class FormIntegrationsComponent implements OnChanges {
  @Input() sections: FormSection[];
  @Input() activeIntegrations: FormIntegrationProvider[];

  @Input() set integrations(value: FormIntegration[]) {
    if (this._integrations) {
      this.integrationsChanged.emit(value);
    }
    this._integrations = value;
  }

  get integrations() {
    return this._integrations;
  }

  @Output() integrationsChanged = new EventEmitter<FormIntegration[]>();


  providerMapping: ProviderMapping = {
    [ FormIntegrationProvider.GREEN_VALLEY ]: {
      enabled: false,
      integration: null,
    },
  };
  FormIntegrationProvider = FormIntegrationProvider;

  private _integrations: FormIntegration[];

  constructor() {
  }

  ngOnChanges(changes: SimpleChanges): void {
    if (changes.integrations) {
      this.setProviderMapping();
    }
  }

  toggleIntegration(provider: FormIntegrationProvider) {
    const existingIntegration = this.integrations.find(i => i.provider === provider);
    if (existingIntegration) {
      this.integrations = updateItem(this.integrations, {
        ...existingIntegration,
        enabled: this.providerMapping[ provider ].enabled,
      }, 'provider');
    } else {
      this.integrations = [ ...this.integrations, this.getNewProvider(provider) ];
    }
    this.setProviderMapping();
  }

  private getNewProvider(provider: FormIntegrationProvider): FormIntegration {
    switch (provider) {
      case FormIntegrationProvider.GREEN_VALLEY:
        return { provider, enabled: true, configuration: { type_id: null, mapping: [] } };
    }
  }

  private setProviderMapping() {
    for (const integration of this.integrations) {
      this.providerMapping[ integration.provider ] = { enabled: integration.enabled, integration };
    }
  }

  updateIntegration(integration: FormIntegration, event: GVIntegrationFormConfig) {
    this.integrations = updateItem(this.integrations, { ...integration, configuration: event }, 'provider');
  }
}
