import { HttpClient } from '@angular/common/http';
import { ChangeDetectionStrategy, Component, OnInit } from '@angular/core';
import { FormControl, FormGroup, Validators } from '@angular/forms';
import { ErrorService } from '@oca/web-shared';
import { IFormGroup } from '@rxweb/types';
import { Subject } from 'rxjs';

export enum QMaticRequiredField {
  EMAIL = 'email',
  PHONE_NUMBER = 'phone-number'
}

interface QMaticSettings {
  url: string | null;
  auth_token: string | null;
  required_fields: QMaticRequiredField[];
  show_product_info: boolean;
  first_step_location: boolean;
}

@Component({
  selector: 'oca-qmatic-settings',
  templateUrl: './qmatic-settings.component.html',
  styleUrls: ['./qmatic-settings.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class QMaticSettingsComponent implements OnInit {
  formGroup = new FormGroup({
    url: new FormControl(null, Validators.required),
    auth_token: new FormControl(null, Validators.required),
    required_fields: new FormControl([]),
    show_product_info: new FormControl(false),
    first_step_location: new FormControl(false),
  }) as IFormGroup<QMaticSettings>;
  possibleRequiredFields = [
    { value: QMaticRequiredField.EMAIL, label: 'oca.Email' },
    { value: QMaticRequiredField.PHONE_NUMBER, label: 'oca.phone_number' },
  ];
  loading$ = new Subject<boolean>();

  constructor(private http: HttpClient,
              private errorService: ErrorService) {
  }

  ngOnInit(): void {
    this.http.get<QMaticSettings>('/common/q-matic').subscribe(result => {
      this.formGroup.setValue(result);
    });
    this.loading$.subscribe(loading => {
      if (loading) {
        this.formGroup.disable();
      } else {
        this.formGroup.enable();
      }
    });
  }

  saveSettings() {
    if (this.formGroup.valid) {
      this.loading$.next(true);
      this.http.put<QMaticSettings>('/common/q-matic', this.formGroup.value).subscribe(() => {
        this.loading$.next(false);
      }, err => {
        this.loading$.next(false);
        const msg = this.errorService.getMessage(err);
        this.errorService.showErrorDialog(msg);
      });
    }
  }
}
