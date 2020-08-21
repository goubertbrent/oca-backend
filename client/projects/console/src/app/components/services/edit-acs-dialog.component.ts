import { ChangeDetectionStrategy, Component, Inject, OnInit } from '@angular/core';
import { FormControl } from '@angular/forms';
import { MatChipInputEvent } from '@angular/material/chips';
import { MAT_DIALOG_DATA, MatDialogRef } from '@angular/material/dialog';
import { Observable } from 'rxjs';
import { map, startWith } from 'rxjs/operators';
import { SERVICE_IDENTITY_REGEX } from '../../constants';
import { AutoConnectedService, Language, LANGUAGES } from '../../interfaces';
import { cloneDeep } from '../../util';

export interface EditAutoConnectedServiceDialogData {
  isNew: boolean;
  acs: AutoConnectedService;
}

@Component({
  selector: 'rcc-edit-acs-dialog',
  changeDetection: ChangeDetectionStrategy.OnPush,
  templateUrl: 'edit-acs-dialog.component.html',
  styles: [ ` .form-row mat-select, .form-row mat-form-field {
    width: 300px;
  }` ],
})
export class EditAutoConnectedServiceDialogComponent implements OnInit {
  languageFormControl = new FormControl();
  isNew: boolean;
  autoConnectedService: AutoConnectedService;
  serviceIdentityRegex = SERVICE_IDENTITY_REGEX;
  filteredLanguages: Observable<Language[]>;

  constructor(private dialogRef: MatDialogRef<EditAutoConnectedServiceDialogComponent>,
              @Inject(MAT_DIALOG_DATA) private data: EditAutoConnectedServiceDialogData) {
  }

  ngOnInit() {
    this.isNew = this.data.isNew;
    this.autoConnectedService = cloneDeep(this.data.acs);
    this.filteredLanguages = this.languageFormControl.valueChanges.pipe(
      startWith(''),
      map(val => val ? this.filterLanguages(val) : LANGUAGES.slice()),
    );
  }

  getLanguage(code: string) {
    const lang = LANGUAGES.find(l => l.code === code);
    return lang ? lang.name : null;
  }

  addLocale(event: MatChipInputEvent) {
    if (!this.autoConnectedService.local.includes(event.value) && this.getLanguage(event.value)) {
      this.autoConnectedService.local = [ ...this.autoConnectedService.local, event.value ];
    }
    this.languageFormControl.reset();
  }

  removeLocale(locale: string) {
    this.autoConnectedService.local = this.autoConnectedService.local.filter(l => l !== locale);
  }

  cancel() {
    this.dialogRef.close();
  }

  submit() {
    this.dialogRef.close(this.autoConnectedService);
  }

  private filterLanguages(val: string): Language[] {
    const re = new RegExp(val, 'gi');
    return LANGUAGES.filter(lang => re.test(lang.name) || re.test(lang.code));
  }

}
