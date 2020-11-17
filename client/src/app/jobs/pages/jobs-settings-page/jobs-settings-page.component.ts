import { ChangeDetectionStrategy, Component, OnDestroy, OnInit, ViewChild } from '@angular/core';
import { FormBuilder, FormControl, FormGroupDirective, NgForm, NgModel, Validators } from '@angular/forms';
import { MatChipInputEvent } from '@angular/material/chips';
import { ErrorStateMatcher } from '@angular/material/core';
import { select, Store } from '@ngrx/store';
import { IFormBuilder, IFormGroup } from '@rxweb/types';
import { Observable, Subject } from 'rxjs';
import { debounceTime, takeUntil } from 'rxjs/operators';
import { filterNull } from '../../../shared/util';
import { JobNotificationType, JobsSettings } from '../../jobs';
import { GetJobSettingsAction, UpdateJobSettingsAction } from '../../jobs.actions';
import { areJobSettingsLoading, getJobsSettings, JobsState } from '../../jobs.state';


/**
 * Ignores the actual form control it's bound to, and uses another model instead
 */
class EmailErrorStateMatcher implements ErrorStateMatcher {
  constructor(private input: NgModel) {
  }

  isErrorState(control: FormControl | null, form: FormGroupDirective | NgForm | null): boolean {
    return (this.input.touched && this.input.invalid) ?? false;
  }

}

@Component({
  selector: 'oca-jobs-settings-page',
  templateUrl: './jobs-settings-page.component.html',
  styleUrls: ['./jobs-settings-page.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class JobsSettingsPageComponent implements OnInit, OnDestroy {
  @ViewChild('emailInput', { static: true }) emailInput: NgModel;
  loading$: Observable<boolean>;
  notificationTypes = [
    { label: 'oca.new_solicitations', description: 'oca.job_notifications_new_description', value: JobNotificationType.NEW_SOLICITATION },
    { label: 'oca.hourly_summary', description: 'oca.job_notifications_hourly_description', value: JobNotificationType.HOURLY_SUMMARY },
  ];
  formGroup: IFormGroup<JobsSettings>;
  destroyed$ = new Subject();
  emailErrorMatcher: ErrorStateMatcher;
  lastSave = 0;
  AUTOSAVE_DELAY = 2000;

  constructor(private store: Store<JobsState>,
              private fb: FormBuilder) {
    const formBuilder: IFormBuilder = fb;
    this.formGroup = formBuilder.group<JobsSettings>({
      emails: formBuilder.control<string[]>([], [Validators.email]),
      notifications: formBuilder.control([], []),
    });
    this.formGroup.valueChanges.pipe(
      takeUntil(this.destroyed$),
      debounceTime(this.AUTOSAVE_DELAY),
    ).subscribe(() => {
      if (this.lastSave + this.AUTOSAVE_DELAY < new Date().getTime()) {
        this.save();
      }
    });
  }

  ngOnInit(): void {
    this.store.dispatch(new GetJobSettingsAction());
    this.loading$ = this.store.pipe(select(areJobSettingsLoading));
    this.store.pipe(select(getJobsSettings), filterNull(), takeUntil(this.destroyed$)).subscribe(settings => {
      this.formGroup.setValue(settings, { emitEvent: false });
    });
    this.emailErrorMatcher = new EmailErrorStateMatcher(this.emailInput);
  }

  ngOnDestroy(): void {
    this.destroyed$.next();
    this.destroyed$.complete();
  }

  addEmail($event: MatChipInputEvent) {
    if (this.emailInput.invalid) {
      this.emailInput.control.markAsTouched();
      return;
    }
    const currentEmails = this.formGroup.controls.emails.value!;
    const newEmail = $event.value?.trim();
    if (newEmail && !currentEmails.includes(newEmail)) {
      this.formGroup.controls.emails.setValue([...currentEmails, newEmail]);
    }
    this.emailInput.reset('');
  }

  removeEmail(email: string) {
    this.formGroup.controls.emails.setValue(this.formGroup.controls.emails.value!.filter(e => e !== email));
  }

  save() {
    if (this.formGroup.valid && this.emailInput.valid) {
      this.lastSave = new Date().getTime();
      this.store.dispatch(new UpdateJobSettingsAction(this.formGroup.value!));
    }
  }
}
