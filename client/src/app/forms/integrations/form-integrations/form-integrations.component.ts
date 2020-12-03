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
  FormIntegration,
  FormIntegrationConfiguration,
  FormIntegrationEmail,
  FormIntegrationGreenValley,
  FormIntegrationProvider,
  FormIntegrationTOPDesk,
  GVIntegrationFormConfig,
  TOPDeskIntegrationConfig,
} from '../integrations';

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
  [ FormIntegrationProvider.TOPDESK ]: {
    enabled: boolean;
    visible: boolean;
    integration: FormIntegrationTOPDesk | null;
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
    [ FormIntegrationProvider.TOPDESK ]: {
      enabled: false,
      visible: false,
      integration: null,
    },
  };
  @Output() integrationsChanged = new EventEmitter<FormIntegration[]>();

  get integrations() {
    return this._integrations;
  }

  @Input() set integrations(value: FormIntegration[]) {
    if (this._integrations) {
      this.integrationsChanged.emit(value);
    }
    this._integrations = value;
  }

  FormIntegrationProvider = FormIntegrationProvider;

  private _integrations: FormIntegration[];

  constructor() {
  }

  ngOnChanges(changes: SimpleChanges): void {
    if (changes.activeIntegrations) {
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
      this.integrations = [...this.integrations, this.getNewProvider(provider)];
    }
    this.setProviderMapping();
  }

  updateIntegration(integration: FormIntegration, event: GVIntegrationFormConfig | EmailIntegrationConfig | TOPDeskIntegrationConfig) {
    // @ts-ignore
    this.integrations = updateItem(this.integrations, { ...integration, configuration: event }, 'provider');
  }

  private getNewProvider(provider: FormIntegrationProvider): FormIntegration {
    switch (provider) {
      case FormIntegrationProvider.GREEN_VALLEY:
        return { provider, enabled: true, visible: true, configuration: { type_id: null, mapping: [] } };
      case FormIntegrationProvider.EMAIL:
        return { provider, enabled: true, visible: true, configuration: { email_groups: [], default_group: null, mapping: [] } };
      case FormIntegrationProvider.TOPDESK:
        return { provider, enabled: true, visible: true, configuration: { mapping: [] } };
    }
  }

  private setProviderMapping() {
    for (const integration of this.activeIntegrations) {
      // @ts-ignore
      this.providerMapping[ integration.provider ] = {
        ...this.providerMapping[ integration.provider ],
        visible: integration.visible,
      };
    }
    for (const { provider, enabled, configuration } of this.integrations) {
      this.providerMapping[ provider ] = {
        ...this.providerMapping[ provider ],
        enabled,
        // @ts-ignore
        integration: { provider, configuration },
      };
    }
  }
}
