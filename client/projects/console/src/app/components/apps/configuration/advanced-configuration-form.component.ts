import { ChangeDetectionStrategy, Component, EventEmitter, Input, Output } from '@angular/core';
import { NgForm } from '@angular/forms';
import { ApiRequestStatus } from '../../../../../framework/client/rpc';
import { EmbeddedApp, RogerthatApp } from '../../../interfaces';

@Component({
  selector: 'rcc-app-advanced-configuration-form',
  changeDetection: ChangeDetectionStrategy.OnPush,
  templateUrl: 'advanced-configuration-form.component.html',
})
export class AppAdvancedConfigurationFormComponent {
  @Input() status: ApiRequestStatus;
  @Input() embeddedApps: EmbeddedApp[];
  @Output() save = new EventEmitter<RogerthatApp>();

  private _app: RogerthatApp;

  get app() {
    return this._app;
  }

  @Input() set app(value: RogerthatApp) {
    this._app = { ...value };
  }

  submit(form: NgForm) {
    if (form.form.valid) {
      this.save.emit({ ...this.app });
    }
  }
}
