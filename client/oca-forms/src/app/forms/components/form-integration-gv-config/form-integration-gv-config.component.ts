import { ChangeDetectionStrategy, Component, EventEmitter, Input, Output } from '@angular/core';
import { NgForm } from '@angular/forms';
import { GVIntegrationConfig } from '../../interfaces/integrations';

@Component({
  selector: 'oca-form-integration-gv-config',
  templateUrl: './form-integration-gv-config.component.html',
  styleUrls: [ './form-integration-gv-config.component.scss' ],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class FormIntegrationGvConfigComponent {
  @Input() configuration: GVIntegrationConfig;
  @Output() configurationChanged = new EventEmitter<GVIntegrationConfig>();

  showPassword = false;

  save(form: NgForm) {
    if (form.form.valid) {
      this.configurationChanged.emit(this.configuration);
    }
  }
}
