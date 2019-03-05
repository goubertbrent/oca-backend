import { AfterViewInit, Component, ElementRef, EventEmitter, Input, OnChanges, Output, SimpleChanges, ViewChild } from '@angular/core';
import { NgForm } from '@angular/forms';
import { MatSlideToggleChange } from '@angular/material';
import { TranslateService } from '@ngx-translate/core';
import { FormSettings, OcaForm } from '../interfaces/forms.interfaces';
import { UserDetailsTO } from '../users/interfaces';

@Component({
  selector: 'oca-edit-form-tombola',
  templateUrl: './edit-form-tombola.component.html',
  styleUrls: [ './edit-form-tombola.component.scss' ],
})
export class EditFormTombolaComponent implements OnChanges, AfterViewInit {
  @ViewChild('ngForm') ngForm: NgForm;
  @ViewChild('timeInput') timeInput: ElementRef<HTMLInputElement>;

  @Input() set form(value: OcaForm) {
    this._form = value;
  };

  get form() {
    return this._form;
  }

  @Input() tombolaWinners: UserDetailsTO[];
  @Output() save = new EventEmitter<OcaForm>();
  settings: FormSettings;
  hasTombola = false;
  minDate: Date;
  dateInput: Date;

  private _form: OcaForm;

  constructor(private _translate: TranslateService) {
    const minDate = new Date();
    minDate.setDate(minDate.getDate() + 1);
    this.minDate = minDate;
    this.dateInput = minDate;
  }

  ngOnChanges(changes: SimpleChanges): void {
    if (changes && changes.form && changes.form.currentValue) {
      this.settings = { ...changes.form.currentValue.settings };
      this.hasTombola = this.settings.tombola != null;
      if (this.settings.visible_until) {
        this.dateInput = new Date(this.settings.visible_until);
        this.setTimeInput();
      }
    }
  }

  ngAfterViewInit() {
    this.setTimeInput();
  }

  toggleTombola(event: MatSlideToggleChange) {
    this.hasTombola = event.checked;
    if (event.checked) {
      this.settings.tombola = {
        winner_message: this._translate.instant('oca.default_tombola_winner_message'),
        winner_count: 1,
      };
    } else {
      this.settings.tombola = null;
      this.saveChanges();
    }
  }

  updateDate() {
    if (this.dateInput) {
      this.settings.visible_until = new Date(this.dateInput.getTime());
      const timeDate = this.timeInput.nativeElement.valueAsDate as Date | undefined;
      if (timeDate) {
        this.settings.visible_until.setHours(timeDate.getUTCHours());
        this.settings.visible_until.setMinutes(timeDate.getUTCMinutes());
      }
    } else {
      this.settings.visible_until = null;
    }
  }

  saveChanges() {
    if (this.ngForm.valid) {
      this.save.emit({ ...this.form, settings: this.settings });
    }
  }

  trackByWinner(index: number, value: UserDetailsTO) {
    return value.email;
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
