import {
  AfterViewInit,
  ChangeDetectionStrategy,
  ChangeDetectorRef,
  Component,
  ElementRef,
  EventEmitter,
  Input,
  OnChanges,
  Output,
  QueryList,
  SimpleChanges,
  ViewChild,
  ViewChildren,
} from '@angular/core';
import { NgForm } from '@angular/forms';
import { MatDialog, MatInput, MatSlideToggleChange } from '@angular/material';
import { TranslateService } from '@ngx-translate/core';
import { SimpleDialogComponent, SimpleDialogData, SimpleDialogResult } from '../../../dialog/simple-dialog.component';
import { CreateDynamicForm, DynamicForm, FormSection, isCreateForm, OcaForm } from '../../../interfaces/forms.interfaces';
import { ArrangeSectionsDialogComponent } from '../arange-sections-dialog/arrange-sections-dialog.component';

@Component({
  selector: 'oca-edit-form',
  templateUrl: './edit-form.component.html',
  styleUrls: [ './edit-form.component.scss' ],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class EditFormComponent implements OnChanges, AfterViewInit {
  @ViewChild('formElement') formElement: NgForm;
  @ViewChild('timeInput') timeInput: ElementRef<HTMLInputElement>;
  @ViewChildren(MatInput) inputs: QueryList<MatInput>;
  @Input() form: OcaForm<CreateDynamicForm> | OcaForm<DynamicForm>;
  @Output() save = new EventEmitter<OcaForm>();
  @Output() create = new EventEmitter<OcaForm<CreateDynamicForm>>();
  minDate: Date;
  hasEndDate = true;
  hasTombola = false;
  dateInput = new Date();

  constructor(private _translate: TranslateService,
              private _matDialog: MatDialog,
              private _changeDetectorRef: ChangeDetectorRef) {
    this.setMinDate();
  }

  ngOnChanges(changes: SimpleChanges): void {
    if (changes.form && changes.form.currentValue) {
      this.hasTombola = this.form.settings.tombola != null;
      if (this.form.settings.visible_until) {
        this.dateInput = new Date(this.form.settings.visible_until);
        this.hasEndDate = true;
        this.setTimeInput();
      } else {
        this.hasEndDate = false;
      }
    }
  }

  ngAfterViewInit() {
    if (this.hasEndDate) {
      this.setTimeInput();
    }
  }

  visibleChanged(event: MatSlideToggleChange) {
    this.form.settings.visible = event.checked;
    if (event.checked) {
      // set timeInput value in next change detection cycle
      setTimeout(() => this.setTimeInput(), 0);
    }
  }

  limitResponsesChanged(event: MatSlideToggleChange) {
    this.form.form.max_submissions = event.checked ? 1 : -1;
  }

  addSection() {
    const id = this.getNextSectionId(this.form.form.sections);
    const title = this._translate.instant('oca.untitled_section');
    this.form.form.sections.push({ id, title, components: [], branding: null });
  }

  moveSection() {
    // scroll to top else the draggables bug out in the dialog
    window.scrollTo(0, 0);
    this._matDialog.open(ArrangeSectionsDialogComponent, { data: this.form.form.sections }).afterClosed().subscribe(result => {
      if (result) {
        this.form.form.sections = result;
        this._changeDetectorRef.markForCheck();
      }
    });
  }

  deleteSection(index: number, section: FormSection) {
    const data: SimpleDialogData = {
      message: this._translate.instant('oca.confirm_delete_section', { title: section.title }),
      ok: this._translate.instant('oca.yes'),
      cancel: this._translate.instant('oca.no'),
    };
    this._matDialog.open(SimpleDialogComponent, { data }).afterClosed().subscribe((result: SimpleDialogResult) => {
      if (result && result.submitted) {
        this.form.form.sections.splice(index, 1);
        this._changeDetectorRef.markForCheck();
      }
    });
  }

  toggleSubmissionSection(event: MatSlideToggleChange) {
    if (event.checked) {
      this.form.form.submission_section = {
        title: this._translate.instant('oca.thank_you'),
        description: this._translate.instant('oca.your_response_has_been_recorded'),
        components: [],
        branding: null,
      };
    } else {
      this.form.form.submission_section = null;
    }
  }

  updateDate() {
    if (this.dateInput) {
      this.form.settings.visible_until = new Date(this.dateInput.getTime());
      const timeDate = this.timeInput.nativeElement.valueAsDate as Date | undefined;
      if (timeDate) {
        this.form.settings.visible_until.setHours(timeDate.getUTCHours());
        this.form.settings.visible_until.setMinutes(timeDate.getUTCMinutes());
      }
    } else {
      this.form.settings.visible_until = null;
    }
  }

  toggleEndDate() {
    if (this.form.settings.visible_until) {
      this.form.settings.visible_until = null;
    } else {
      this.dateInput = new Date(this.minDate);
      this.form.settings.visible_until = this.dateInput;
    }
    this.hasEndDate = !!this.form.settings.visible_until;
  }

  toggleTombola(event: MatSlideToggleChange) {
    this.hasTombola = event.checked;
    if (event.checked) {
      this.setMinDate();
      if (!this.hasEndDate) {
        this.toggleEndDate();
      }
      this.form = {
        form: {
          ...this.form.form,
          max_submissions: 1,
        },
        settings: {
          ...this.form.settings,
          tombola: {
            winner_message: this._translate.instant('oca.default_tombola_winner_message'),
            winner_count: 1,
          },
        },
      };
      // setTimeout needed because the view is not created yet at this moment
      setTimeout(() => this.setTimeInput());
    } else {
      this.form.settings.tombola = null;
    }
  }

  saveForm() {
    if (!this.formElement.valid) {
      for (const control of Object.values(this.formElement.controls)) {
        if (!control.valid) {
          control.markAsTouched();
          control.markAsDirty();
          control.updateValueAndValidity();
        }
      }
      const invalidInput = this.inputs.find(input => input.errorState);
      if (invalidInput) {
        invalidInput.focus();
      }
      this._matDialog.open(SimpleDialogComponent, {
        data: {
          title: this._translate.instant('oca.error'),
          message: this._translate.instant('oca.some_fields_are_invalid'),
          ok: this._translate.instant('oca.ok'),
        } as SimpleDialogData,
      });
      return;
    }
    if (isCreateForm(this.form)) {
      this.create.emit(this.form);
    } else {
      this.save.emit(this.form);
    }
  }

  trackBySection(index: number, section: FormSection) {
    return section.id;
  }

  private setMinDate() {
    const minDate = new Date();
    minDate.setDate(minDate.getDate() + 1);
    this.minDate = minDate;
  }

  private getNextSectionId(sections: FormSection[]) {
    const takenIds = sections.map(s => s.id);
    let nextId = sections.length + 1;
    while (takenIds.includes(nextId.toString())) {
      nextId += 1;
    }
    return nextId.toString();
  }

  private setTimeInput() {
    if (this.timeInput) {
      const d = new Date(0);
      d.setUTCHours(this.dateInput.getHours());
      d.setUTCMinutes(this.dateInput.getMinutes());
      this.timeInput.nativeElement.valueAsDate = d;
    }
  }
}
