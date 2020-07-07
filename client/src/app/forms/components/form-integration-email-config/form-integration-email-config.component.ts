import { ChangeDetectionStrategy, Component, EventEmitter, Input, Output } from '@angular/core';
import { NgForm } from '@angular/forms';
import { EmailIntegrationConfig } from '../../interfaces/integrations';

@Component({
  selector: 'oca-form-integration-email-config',
  templateUrl: './form-integration-email-config.component.html',
  styleUrls: ['./form-integration-email-config.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class FormIntegrationEmailConfigComponent {
  @Input() configuration: EmailIntegrationConfig;
  @Output() configurationChanged = new EventEmitter<EmailIntegrationConfig>();

  save(form: NgForm) {
    if (form.form.valid) {
      this.configurationChanged.emit(this.configuration);
    }
  }
}
