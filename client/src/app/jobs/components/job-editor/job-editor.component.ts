import {
  AfterViewInit,
  ChangeDetectionStrategy,
  Component,
  EventEmitter,
  Input,
  OnDestroy,
  Output,
  QueryList,
  ViewChildren,
} from '@angular/core';
import { FormBuilder, Validators } from '@angular/forms';
import { MatDialog, MatDialogConfig } from '@angular/material/dialog';
import { MatInput } from '@angular/material/input';
import { MatSelect } from '@angular/material/select';
import { TranslateService } from '@ngx-translate/core';
import { SimpleDialogComponent, SimpleDialogData, SimpleDialogResult } from '@oca/web-shared';
import { IFormBuilder, IFormGroup } from '@rxweb/types';
import { Subject } from 'rxjs';
import { takeUntil } from 'rxjs/operators';
import { EASYMDE_OPTIONS } from '../../../../environments/config';
import {
  CONTRACT_TYPES,
  ContractType,
  EditJobOffer,
  JOB_DOMAINS,
  JobDomain,
  JobMatched,
  JobMatchSource,
  JobOfferContactInformation,
  JobOfferContract,
  JobOfferEmployer,
  JobOfferFunction,
  JobOfferLocation,
  JobStatus,
} from '../../jobs';
import { PublishJobDialogComponent, PublishJobDialogResult } from '../publish-job-dialog/publish-job-dialog.component';
import { UnPublishJobDialogComponent } from '../un-publish-job-dialog/un-publish-job-dialog.component';

@Component({
  selector: 'oca-job-editor',
  templateUrl: './job-editor.component.html',
  styleUrls: ['./job-editor.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class JobEditorComponent implements AfterViewInit, OnDestroy {
  @ViewChildren(MatSelect) selects: QueryList<MatSelect>;
  @ViewChildren(MatInput) inputs: QueryList<MatInput>;
  @Output() submitted = new EventEmitter<EditJobOffer>();
  @Output() createNewsItem = new EventEmitter();
  @Input() isExistingJob = false;
  EASYMDE_OPTIONS = EASYMDE_OPTIONS;
  JOB_DOMAINS = JOB_DOMAINS;
  CONTRACT_TYPES = CONTRACT_TYPES;
  formGroup: IFormGroup<EditJobOffer>;

  canSave = true;
  canPublish = false;
  canUnPublish = false;
  canRemove = false;

  private destroyed$ = new Subject();
  private formBuilder: IFormBuilder;

  constructor(formBuilder: FormBuilder,
              private translate: TranslateService,
              private matDialog: MatDialog) {
    this.formBuilder = formBuilder;
    this.formGroup = this.formBuilder.group<EditJobOffer>({
      employer: this.formBuilder.group<JobOfferEmployer>({
        name: this.formBuilder.control('', Validators.required),
      }),
      function: this.formBuilder.group<JobOfferFunction>({
        title: this.formBuilder.control('', [Validators.required]),
        description: this.formBuilder.control('', [Validators.required]),
      }),
      job_domains: this.formBuilder.control<JobDomain[]>([], Validators.required),
      location: this.formBuilder.group<JobOfferLocation>({
        city: this.formBuilder.control('', Validators.required),
        street: this.formBuilder.control('', Validators.required),
        street_number: this.formBuilder.control('', Validators.required),
        country_code: this.formBuilder.control('', Validators.required),
        postal_code: this.formBuilder.control('', Validators.required),
        geo_location: this.formBuilder.control(null),
      }),
      contract: this.formBuilder.group<JobOfferContract>({
        type: this.formBuilder.control(ContractType.FULLTIME, Validators.required),
      }),
      contact_information: this.formBuilder.group<JobOfferContactInformation>({
        email: this.formBuilder.control('', [Validators.required, Validators.email]),
        phone_number: this.formBuilder.control('', Validators.required),
      }),
      profile: this.formBuilder.control('', Validators.required),
      details: this.formBuilder.control('', [Validators.required]),
      status: this.formBuilder.control(null, Validators.required),
      start_date: this.formBuilder.control(null),
      match: this.formBuilder.group<JobMatched>({
        source: this.formBuilder.control(JobMatchSource.NO_MATCH),
        platform: this.formBuilder.control(null),
      }),
    });
  }

  private _disabled = false;

  get disabled() {
    return this._disabled;
  }

  get functionFormGroup() {
    return this.formGroup.controls.function as IFormGroup<JobOfferFunction>;
  }

  @Input() set disabled(value: boolean) {
    // Disable all controls while loading / saving
    if (value) {
      this.formGroup.disable();
    } else {
      this.formGroup.enable();
    }
    this._disabled = value;
  }

  @Input() set value(value: EditJobOffer) {
    this.formGroup.setValue(value);
    this.setButtons();
  }

  ngAfterViewInit(): void {
    this.formGroup.controls.status.valueChanges.pipe(takeUntil(this.destroyed$)).subscribe(() => {
      this.setButtons();
    });
  }

  ngOnDestroy(): void {
    this.destroyed$.next();
    this.destroyed$.complete();
  }

  submit() {
    if (this.checkValidity()) {
      this.submitted.emit(this.formGroup.value!);
    } else {
      const config: MatDialogConfig<SimpleDialogData> = {
        data: {
          ok: this.translate.instant('oca.ok'),
          message: this.translate.instant('oca.please_fill_in_required_fields'),
        },
      };
      this.matDialog.open(SimpleDialogComponent, config);
    }
  }

  publish() {
    if (!this.checkValidity()) {
      return;
    }
    const val = this.formGroup.controls.start_date.value;
    const date = val ? new Date(val) : null;
    this.matDialog.open(PublishJobDialogComponent, { data: { date } })
      .afterClosed().subscribe((result?: PublishJobDialogResult) => {
      if (result) {
        if (result.publishNow) {
          this.setStatusAndSubmit(JobStatus.ONGOING);
        } else {
          this.formGroup.controls.start_date.setValue(result.date.toISOString());
          this.submit();
        }
      }
    });
  }

  unPublish() {
    this.matDialog.open(UnPublishJobDialogComponent).afterClosed().subscribe((result?: JobMatched) => {
      if (result) {
        this.formGroup.controls.match.setValue(result);
        this.setStatusAndSubmit(JobStatus.HIDDEN);
      }
    });
  }

  remove() {
    const data: SimpleDialogData = {
      ok: this.translate.instant('oca.Yes'),
      cancel: this.translate.instant('oca.Cancel'),
      message: this.translate.instant('oca.confirm_delete_job'),
      title: this.translate.instant('oca.confirmation'),
    };
    this.matDialog.open(SimpleDialogComponent, { data }).afterClosed().subscribe((result: SimpleDialogResult) => {
      if (result?.submitted) {
        this.setStatusAndSubmit(JobStatus.DELETED);
      }
    });
  }

  private setButtons() {
    if (!this.isExistingJob) {
      return;
    }
    const status = this.formGroup.controls.status.value as JobStatus;
    const match = this.formGroup.controls.match.value as JobMatched | null;
    // In case there was a match you can never update this job offer anymore
    this.canSave = !match || match.source === JobMatchSource.NO_MATCH;
    // Can only publish in case status is NEW or HIDDEN and when there was no match in the past
    this.canPublish = status === JobStatus.NEW || (status === JobStatus.HIDDEN && (!match || match.source === JobMatchSource.NO_MATCH));
    this.canUnPublish = status === JobStatus.ONGOING;
    this.canRemove = status === JobStatus.HIDDEN;
  }

  private setStatusAndSubmit(status: JobStatus) {
    // Only update the status in case everything else is ok, and then immediately save
    if (this.checkValidity()) {
      this.formGroup.controls.status.setValue(status);
      this.submitted.emit(this.formGroup.value!);
    }
  }

  private checkValidity(): boolean {
    if (this.formGroup.valid) {
      return true;
    }
    this.formGroup.markAllAsTouched();
    // Focus first invalid select or input
    const invalidSelect = this.selects.find(select => select.errorState);
    if (invalidSelect) {
      invalidSelect.focus();
    } else {
      const invalidInput = this.inputs.find(input => input.errorState);
      if (invalidInput) {
        invalidInput.focus();
      }
    }
    return false;
  }
}
