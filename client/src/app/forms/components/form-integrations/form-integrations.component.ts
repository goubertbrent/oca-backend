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
import { updateItem } from '../../../shared/util';
import { FormSection } from '../../interfaces/forms';
import {
  EmailIntegrationConfig,
  FormIntegration, FormIntegrationConfiguration,
  FormIntegrationEmail,
  FormIntegrationGreenValley,
  FormIntegrationProvider,
  GVIntegrationFormConfig,
} from '../../interfaces/integrations';

interface ProviderMapping {
  [ FormIntegrationProvider.GREEN_VALLEY ]: {
    enabled: boolean;
    visible: boolean;
    integration: FormIntegrationGreenValley | null;
  };
  [ FormIntegrationProvider.EMAIL ]: {
    enabled: boolean;
    visible: boolean;
    integration: FormIntegrationEmail | null;
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
  @Input() activeIntegrations: FormIntegrationConfiguration[];

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
      visible: false,
      integration: null,
    },
    [ FormIntegrationProvider.EMAIL ]: {
      enabled: false,
      visible: true,
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

  updateIntegration(integration: FormIntegration, event: GVIntegrationFormConfig | EmailIntegrationConfig) {
    // @ts-ignore
    this.integrations = updateItem(this.integrations, { ...integration, configuration: event }, 'provider');
  }

  private getNewProvider(provider: FormIntegrationProvider): FormIntegration {
    switch (provider) {
      case FormIntegrationProvider.GREEN_VALLEY:
        return { provider, enabled: true, visible: true, configuration: { type_id: null, mapping: [] } };
      case FormIntegrationProvider.EMAIL:
        return { provider, enabled: true, visible: true, configuration: { email_groups: [], default_group: null, mapping: [] } };
    }
  }

  private setProviderMapping() {
    for (const integration of this.integrations) {
      // @ts-ignore
      this.providerMapping[ integration.provider ] = { enabled: integration.enabled, visible: integration.visible, integration };
    }
  }
}
