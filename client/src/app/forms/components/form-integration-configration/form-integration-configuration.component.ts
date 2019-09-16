import { ChangeDetectionStrategy, Component, EventEmitter, Input, OnChanges, Output, SimpleChanges } from '@angular/core';
import { FormIntegrationConfiguration, FormIntegrationProvider } from '../../interfaces/integrations';

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
      visible: true,
      configuration: {
        base_url: '',
        password: '',
        username: '',
      },
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
