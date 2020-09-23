import { ChangeDetectionStrategy, Component, EventEmitter, Input, Output, ViewEncapsulation } from '@angular/core';
import { NgForm } from '@angular/forms';
import { ApiRequestStatus } from '../../../../../framework/client/rpc';
import { Community } from '../../../communities/community/communities';
import { AppServiceFilter, RogerthatApp } from '../../../interfaces';

@Component({
  selector: 'rcc-app-advanced-configuration-form',
  templateUrl: 'advanced-configuration-form.component.html',
  changeDetection: ChangeDetectionStrategy.OnPush,
  encapsulation: ViewEncapsulation.None,
})
export class AppAdvancedConfigurationFormComponent {
  @Input() status: ApiRequestStatus;
  @Input() communities: Community[];
  @Output() save = new EventEmitter<RogerthatApp>();
  appServiceFilters = [
    { value: AppServiceFilter.COUNTRY, label: 'Filtered by country' },
    { value: AppServiceFilter.COMMUNITIES, label: 'Filtered by communities' },
  ];

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
