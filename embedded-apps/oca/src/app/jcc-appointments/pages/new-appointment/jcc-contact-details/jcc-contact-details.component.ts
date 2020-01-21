import { DatePipe } from '@angular/common';
import { Component, EventEmitter, Input, Output, ViewChild } from '@angular/core';
import { NgForm } from '@angular/forms';
import { markFormGroupTouched } from '../../../../shared/form-utils';
import { AppointmentExtendedDetails, ClientDetails, FORM_FIELDS, JccFormField } from '../../../appointments';


@Component({
  selector: 'app-jcc-contact-details',
  templateUrl: './jcc-contact-details.component.html',
  styleUrls: ['./jcc-contact-details.component.scss'],
})
export class JccContactDetailsComponent {
  @Output() detailsChanged = new EventEmitter<Partial<ClientDetails>>();
  contactDetails: Partial<ClientDetails> = {
    clientMail: rogerthat.user.account,
    clientLastName: rogerthat.user.lastName,
  };
  fields: JccFormField[] = FORM_FIELDS.filter(f => f.IsVisible);
  maxDate = new Date().getFullYear().toString();
  @ViewChild(NgForm, { static: true }) private form: NgForm;
  private defaultValues: Partial<ClientDetails> = {
    clientMail: rogerthat.user.account,
    clientFirstName: rogerthat.user.firstName,
    clientLastName: rogerthat.user.lastName,
    clientInitials: rogerthat.user.firstName,
  };

  constructor(private datePipe: DatePipe) {
  }

  @Input() set requiredFields(value: (keyof AppointmentExtendedDetails)[]) {
    this.fields = FORM_FIELDS.map(field => {
      const fieldName = field.Name;
      const required = value.includes(fieldName);
      const visible = field.IsVisible || required;
      if (visible && field.Name in this.defaultValues) {
        (this.contactDetails as any)[ fieldName ] = (this.defaultValues as any)[ fieldName ];
      }
      return ({ ...field, IsRequired: field.IsRequired || required, IsVisible: visible } as JccFormField);
    }).filter(f => f.IsVisible);
  }

  setDateField(fieldName: keyof AppointmentExtendedDetails, value: Date) {
    this.contactDetails = { ...this.contactDetails, [ fieldName ]: this.datePipe.transform(value, 'yyyy-MM-dd') as string };
    this.detailsChanged.emit(this.contactDetails);
  }

  setField(fieldName: keyof AppointmentExtendedDetails, value: string | null) {
    this.contactDetails = { ...this.contactDetails, [ fieldName ]: value };
    this.detailsChanged.emit(this.contactDetails);
  }

  isValid() {
    markFormGroupTouched(this.form.form);
    const field = this.fields.find(f => f.Name === 'clientDateOfBirth');
    if (field && field.IsRequired) {
      this.form.form.controls.clientDateOfBirth.setErrors(this.form.form.controls.clientDateOfBirth.value ? null : { required: true });
    }
    return this.form.form.valid;
  }
}
