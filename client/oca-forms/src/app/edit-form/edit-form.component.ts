import {
  AfterViewInit,
  ChangeDetectionStrategy,
  Component,
  ElementRef,
  EventEmitter,
  Input,
  OnChanges,
  Output,
  SimpleChanges,
  ViewChild,
} from '@angular/core';
import { NgForm } from '@angular/forms';
import { MatSlideToggleChange } from '@angular/material';
import { TranslateService } from '@ngx-translate/core';
import { CreateDynamicForm, DynamicForm, FormSection, isCreateForm, OcaForm } from '../interfaces/forms.interfaces';

@Component({
  selector: 'oca-edit-form',
  templateUrl: './edit-form.component.html',
  styleUrls: [ './edit-form.component.scss' ],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class EditFormComponent implements OnChanges, AfterViewInit {
  @ViewChild('formElement') formElement: NgForm;
  @ViewChild('timeInput') timeInput: ElementRef<HTMLInputElement>;
  @Input() form: OcaForm<CreateDynamicForm> | OcaForm<DynamicForm>;
  @Output() save = new EventEmitter<OcaForm>();
  @Output() create = new EventEmitter<OcaForm<CreateDynamicForm>>();
  minDate: Date;
  hasEndDate = true;
  dateInput = new Date();

  constructor(private _translate: TranslateService) {
    const minDate = new Date();
    minDate.setDate(minDate.getDate() + 1);
    this.minDate = minDate;
  }

  ngOnChanges(changes: SimpleChanges): void {
    if (changes.form && changes.form.currentValue) {
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
    this.form.form.sections.push({ id, title, components: [] });
  }

  deleteSection(section: FormSection) {
    // TODO confirm
    const index = this.form.form.sections.indexOf(section);
    this.form.form.sections.splice(index, 1);
  }

  toggleSubmissionSection(event: MatSlideToggleChange) {
    if (event.checked) {
      this.form.form.submission_section = {
        title: this._translate.instant('oca.thank_you'),
        description: this._translate.instant('oca.your_response_has_been_recorded'),
        components: [],
      };
    } else {
      this.form.form.submission_section = null;
    }
  }

  updateDate() {
    console.log(this.dateInput);
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
      this.form.settings.visible_until = new Date();
    }
    this.hasEndDate = !!this.form.settings.visible_until;
  }

  saveForm() {
    if (!this.formElement.valid) {
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
