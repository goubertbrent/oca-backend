import { ChangeDetectionStrategy, Component, Inject, OnInit } from '@angular/core';
import { FormControl, FormGroup, Validators } from '@angular/forms';
import { MAT_DIALOG_DATA, MatDialogRef } from '@angular/material/dialog';
import { IFormGroup } from '@rxweb/types';
import { Observable } from 'rxjs';
import { map, startWith, tap } from 'rxjs/operators';
import { Language } from '../../../interfaces';
import { HomeScreenDefaultTranslation } from '../homescreen';

export interface AddTranslationDialogData {
  defaultLanguage: Language;
  defaultTranslations: HomeScreenDefaultTranslation[];
}

export interface AddTranslationDialogResult {
  key: string;
  value: string;
}

export interface DefaultTranslation {
  key: string;
  value: string;
}

@Component({
  selector: 'rcc-add-translation-dialog',
  templateUrl: './add-translation-dialog.component.html',
  styleUrls: ['./add-translation-dialog.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class AddTranslationDialogComponent implements OnInit {
  formGroup = new FormGroup({
      key: new FormControl('', Validators.required),
      value: new FormControl('', Validators.required),
    },
  ) as IFormGroup<AddTranslationDialogResult>;
  language: Language;
  filteredTranslations$: Observable<DefaultTranslation[]>;
  defaultTranslations: DefaultTranslation[];

  constructor(private dialogRef: MatDialogRef<AddTranslationDialogComponent>,
              @Inject(MAT_DIALOG_DATA) private data: AddTranslationDialogData) {
    this.language = data.defaultLanguage;
    this.defaultTranslations = data.defaultTranslations
      .map(({ key, values }) => ({ key, value: values[ data.defaultLanguage.code ] }))
      .sort((first, second) => first.value.localeCompare(second.value));
  }

  ngOnInit() {
    this.filteredTranslations$ = this.formGroup.controls.value.valueChanges.pipe(
      startWith(''),
      map(value => typeof value === 'string' ? value : ''),
      tap(value => {
        const foundDefault = this.defaultTranslations.find(t => t.value === value);
        if (foundDefault) {
          this.formGroup.controls.key.setValue(foundDefault.key, { emitEvent: false });
        }
      }),
      map(value => value ? this.filterDefaultTranslations(value) : this.defaultTranslations),
    );
  }

  closeWithResult() {
    if (this.formGroup.valid) {
      this.dialogRef.close(this.formGroup.value!!);
    }
  }

  private filterDefaultTranslations(value: string) {
    const lowerValue = value.toLowerCase();
    return this.defaultTranslations.filter(t => t.value.toLowerCase().includes(lowerValue));
  }
}
