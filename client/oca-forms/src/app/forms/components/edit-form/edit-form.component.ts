import { StepperSelectionEvent } from '@angular/cdk/stepper';
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
import { MatDialog, MatDialogConfig, MatInput, MatSlideToggleChange } from '@angular/material';
import { TranslateService } from '@ngx-translate/core';
import { SimpleDialogComponent, SimpleDialogData, SimpleDialogResult } from '../../../shared/dialog/simple-dialog.component';
import { UserDetailsTO } from '../../../shared/users/interfaces';
import {
  COMPLETED_STEP_MAPPING,
  CompletedFormStepType,
  FormSection,
  NextActionType,
  OcaForm,
  SaveForm,
  SubmissionSection,
  UINextAction,
} from '../../interfaces/forms.interfaces';
import { ArrangeSectionsDialogComponent } from '../arange-sections-dialog/arrange-sections-dialog.component';

@Component({
  selector: 'oca-edit-form',
  templateUrl: './edit-form.component.html',
  styleUrls: [ './edit-form.component.scss' ],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class EditFormComponent implements AfterViewInit, OnChanges {
  @ViewChild('formElement') formElement: NgForm;
  @ViewChild('timeInput') timeInput: ElementRef<HTMLInputElement>;
  @ViewChildren(MatInput) inputs: QueryList<MatInput>;

  @Input() set value(value: OcaForm) {
    this._form = value;
    this._hasChanges = false;
    this.setNextActions();
  }

  set form(value: OcaForm) {
    this._form = value;
    this._hasChanges = true;
    this.setNextActions();
  }

  get form() {
    return this._form;
  }

  @Output() save = new EventEmitter<SaveForm>();
  @Output() createNews = new EventEmitter();
  @Output() testForm = new EventEmitter<UserDetailsTO>();

  nextActionsMapping: { [ key: string ]: UINextAction[] } = {};
  minDate: Date;
  hasEndDate = true;
  hasTombola = false;
  dateInput = new Date();
  selectedTestUser: UserDetailsTO | undefined;
  completedSteps = [ true, false, false, false, false ];
  stepperIndex = 0;
  hasTested = false;
  STEP_INDEX_TEST = 1;
  STEP_INDEX_LAUNCH = 4;
  private _hasChanges = false;
  private _form: OcaForm;

  constructor(private _translate: TranslateService,
              private _matDialog: MatDialog,
              private _changeDetectorRef: ChangeDetectorRef) {
    this.setMinDate();
  }

  ngAfterViewInit() {
    if (this.hasEndDate) {
      this.setTimeInput();
    }
  }

  ngOnChanges(changes: SimpleChanges): void {
    if (changes.value && changes.value.currentValue) {
      this.hasTombola = this.form.settings.tombola != null;
      if (this.form.settings.visible_until) {
        this.dateInput = new Date(this.form.settings.visible_until);
        this.hasEndDate = true;
        this.setTimeInput();
      } else {
        this.hasEndDate = false;
      }
      const completedStepIds = this.form.settings.steps.map(s => s.step_id);
      for (let i = this.STEP_INDEX_TEST; i < this.completedSteps.length; i++) {
        const hasCompletedStep = completedStepIds.includes(COMPLETED_STEP_MAPPING[ i ]);
        this.completedSteps[ i ] = i === 0 ? true : (hasCompletedStep && this.completedSteps[ i - 1 ]);
        if (hasCompletedStep) {
          this.stepperIndex = i;
        }
      }
      this.hasTested = completedStepIds.includes(CompletedFormStepType.TEST);
    }
  }

  visibleChanged(event: MatSlideToggleChange) {
    const steps = this.form.settings.steps;
    if (!steps.some(s => s.step_id === CompletedFormStepType.LAUNCH)) {
      steps.push({ step_id: CompletedFormStepType.LAUNCH });
    }
    this.form = { ...this.form, settings: { ...this.form.settings, visible: event.checked, steps } };
    if (event.checked) {
      // set timeInput value in next change detection cycle
      setTimeout(() => this.setTimeInput(), 0);
    }
    this.saveForm();
  }

  limitResponsesChanged(event: MatSlideToggleChange) {
    this.form = { ...this.form, form: { ...this.form.form, max_submissions: event.checked ? 1 : -1 } };
  }

  addSection() {
    const id = this.getNextSectionId(this.form.form.sections);
    const title = this._translate.instant('oca.untitled_section');
    const newSection: FormSection = { id, title, components: [], branding: null, next_action: null };
    this.form = { ...this.form, form: { ...this.form.form, sections: [ ...this.form.form.sections, newSection ] } };
  }

  moveSection() {
    // scroll to top else the draggables bug out in the dialog
    window.scrollTo(0, 0);
    this._matDialog.open(ArrangeSectionsDialogComponent, { data: this.form.form.sections }).afterClosed().subscribe(result => {
      if (result) {
        this.form = { ...this.form, form: { ...this.form.form, sections: result } };
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
    let section: SubmissionSection | null = null;
    if (event.checked) {
      section = {
        title: this._translate.instant('oca.thank_you'),
        description: this._translate.instant('oca.your_response_has_been_recorded'),
        components: [],
        branding: null,
      };
    }
    this.form = { ...this.form, form: { ...this.form.form, submission_section: section } };
  }

  updateDate() {
    let visibleUntil: Date | null = null;
    if (this.dateInput) {
      visibleUntil = new Date(this.dateInput.getTime());
      const timeDate = this.timeInput.nativeElement.valueAsDate as Date | undefined;
      if (timeDate) {
        visibleUntil.setHours(timeDate.getUTCHours());
        visibleUntil.setMinutes(timeDate.getUTCMinutes());
      }
    }
    this.form = { ...this.form, settings: { ...this.form.settings, visible_until: visibleUntil } };
  }

  toggleEndDate() {
    let visibleUntil: Date | null = null;
    if (!this.form.settings.visible_until) {
      this.dateInput = new Date(this.minDate);
      visibleUntil = this.dateInput;
    }
    this.form = { ...this.form, settings: { ...this.form.settings, visible_until: visibleUntil } };
    this.hasEndDate = !!this.form.settings.visible_until;
  }

  toggleTombola(event: MatSlideToggleChange) {
    this.hasTombola = event.checked;
    if (event.checked) {
      this.setMinDate();
      if (!this.hasEndDate) {
        this.toggleEndDate();
      }
      const visibleUntil = new Date();
      visibleUntil.setDate(visibleUntil.getDate() + 1);
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
          visible_until: visibleUntil,
        },
      };
      // setTimeout needed because the view is not created yet at this moment
      setTimeout(() => this.setTimeInput());
    } else {
      this.form = { ...this.form, settings: { ...this.form.settings, tombola: null } };
    }
  }

  saveForm(silent?: boolean) {
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
        },
      } as MatDialogConfig<SimpleDialogData>);
      return;
    }
    this.save.emit({ data: this.form, silent });
  }

  onStepChange(event: StepperSelectionEvent) {
    if (event.previouslySelectedIndex === this.STEP_INDEX_TEST) {
      // Adding the completed step is handled by the specific functionality
      return;
    }
    const previousStep = COMPLETED_STEP_MAPPING[ event.previouslySelectedIndex ];
    if (!this.form.settings.steps.some(s => s.step_id === previousStep)) {
      this.form = { ...this.form, settings: { ...this.form.settings, steps: [ ...this.form.settings.steps, { step_id: previousStep } ] } };
    }
    if (this._hasChanges) {
      this.saveForm(true);
    }
  }

  /**
   * Marks the form as 'changed', used for auto-saving when switching between steps.
   */
  markChanged() {
    this.form = { ...this.form };
  }

  trackBySection(index: number, section: FormSection) {
    return section.id;
  }

  onTestUserSelected(user: UserDetailsTO) {
    this.selectedTestUser = user;
  }

  sendTestForm() {
    this.testForm.emit(this.selectedTestUser);
    if (!this.form.settings.steps.some(s => s.step_id === CompletedFormStepType.TEST)) {
      this.form = {
        ...this.form,
        settings: { ...this.form.settings, steps: [ ...this.form.settings.steps, { step_id: CompletedFormStepType.TEST } ] },
      };
      this.saveForm(true);
    }
  }

  private setMinDate() {
    this.minDate = new Date();
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

  private setNextActions() {
    const sectionActions: UINextAction[] = [];
    for (let i = 0; i < this.form.form.sections.length; i++) {
      const section = this.form.form.sections[ i ];
      const sectionNumber = i + 1;
      const sectionTitle = section.title ? `${sectionNumber} (${section.title})` : sectionNumber;
      sectionActions.push({
        label: this._translate.instant('oca.go_to_section_x', { section: sectionTitle }),
        action: {
          type: NextActionType.SECTION,
          section: section.id,
        },
      });
    }
    const nextSection: UINextAction = {
      label: this._translate.instant('oca.continue_to_next_section'),
      action: { type: NextActionType.NEXT },
    };
    const submitSection: UINextAction = {
      label: this._translate.instant('oca.submit_form'),
      action: { type: NextActionType.SUBMIT },
    };
    for (const section of this.form.form.sections) {
      this.nextActionsMapping[ section.id ] = [
        nextSection,
        ...sectionActions.filter(a => a.action.type !== NextActionType.SECTION || a.action.section !== section.id),
        submitSection,
      ];
    }
  }
}
