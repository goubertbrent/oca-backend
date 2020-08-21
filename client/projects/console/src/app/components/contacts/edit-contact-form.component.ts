import { ChangeDetectionStrategy, Component, EventEmitter, Input, Output } from '@angular/core';
import { ApiRequestStatus } from '../../../../framework/client/rpc';
import { Contact } from '../../interfaces';

@Component({
  selector: 'rcc-edit-contact-form',
  changeDetection: ChangeDetectionStrategy.OnPush,
  templateUrl: 'edit-contact-form.component.html',
})
export class EditContactFormComponent {
  @Input() status: ApiRequestStatus;
  @Output() save = new EventEmitter<Contact>();

  private _contact: Contact;

  get contact() {
    return this._contact;
  }

  @Input() set contact(value: Contact) {
    this._contact = { ...value };
  }

  submit() {
    this.save.emit({ ...this.contact });
  }
}
