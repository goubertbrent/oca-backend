import { ChangeDetectionStrategy, Component, EventEmitter, Input, OnChanges, Output, SimpleChanges } from '@angular/core';
import {
  FormIntegrationConfiguration,
  FormIntegrationProvider,
  IntegrationConfigurationEmail,
  IntegrationConfigurationGV,
  IntegrationConfigurationTOPDesk,
} from '../integrations';

@Component({
  selector: 'oca-form-integration-configuration',
  templateUrl: './form-integration-configuration.component.html',
  styleUrls: [ './form-integration-configuration.component.scss' ],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class FormIntegrationConfigurationComponent implements OnChanges {
  @Input() configurations: FormIntegrationConfiguration[];
  @Output() configurationUpdated = new EventEmitter<FormIntegrationConfiguration>();

  FormIntegrationProvider = FormIntegrationProvider;

  configMapping: { [key in FormIntegrationProvider]: FormIntegrationConfiguration } = {
    [ FormIntegrationProvider.GREEN_VALLEY ]: {
      provider: FormIntegrationProvider.GREEN_VALLEY,
      enabled: false,
      can_edit: false,
      configuration: {} as IntegrationConfigurationGV,
    },
    [ FormIntegrationProvider.EMAIL ]: {
      provider: FormIntegrationProvider.EMAIL,
      enabled: false,
      can_edit: true,
      configuration: {} as IntegrationConfigurationEmail,
    },
    [ FormIntegrationProvider.TOPDESK ]: {
      provider: FormIntegrationProvider.TOPDESK,
      enabled: false,
      can_edit: false,
      configuration: {} as IntegrationConfigurationTOPDesk,
    },
  };

  ngOnChanges(changes: SimpleChanges): void {
    if (changes.configurations && this.configurations) {
      for (const conf of this.configurations) {
        this.configMapping[ conf.provider ] = conf;
      }
    }
  }

  integrationToggled(provider: FormIntegrationProvider) {
    this.configurationUpdated.emit(this.configMapping[ provider ]);
  }

  updateConfiguration(integration: FormIntegrationConfiguration, configuration: any) {
    this.configurationUpdated.emit({...integration, configuration});
  }
}
