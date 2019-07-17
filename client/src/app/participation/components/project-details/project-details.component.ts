import { getCurrencySymbol } from '@angular/common';
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
import { deepCopy } from '../../../shared/util/misc';
import { CreateProject, Project } from '../../projects';

@Component({
  selector: 'oca-project-details',
  templateUrl: './project-details.component.html',
  styleUrls: [ './project-details.component.scss' ],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class ProjectDetailsComponent implements OnChanges, AfterViewInit {
  @ViewChild('startTime', { static: true }) startTime: ElementRef<HTMLInputElement>;
  @ViewChild('endTime', { static: true }) endTime: ElementRef<HTMLInputElement>;
  @Input() project: Project | CreateProject;
  @Input() loading = false;
  @Output() saved = new EventEmitter<Project | CreateProject>();
  _project: Project | CreateProject;
  getCurrencySymbol = getCurrencySymbol;

  ngOnChanges(changes: SimpleChanges) {
    if (changes.project && changes.project.currentValue) {
      this._project = deepCopy(this.project);
      this.setDates();
    }
  }

  ngAfterViewInit() {
    this.setDates();
  }

  submit(form: NgForm) {
    if (form.form.valid) {
      this.saved.emit(this._project);
    }
  }

  setTime(propertyName: 'end_date' | 'start_date', target: HTMLInputElement) {
    let date: Date | string = this._project[ propertyName ] || new Date();
    if (!(date instanceof Date)) {
      date = new Date(date);
    }
    const time: Date = target.valueAsDate;
    date.setHours(time.getUTCHours());
    date.setMinutes(time.getUTCMinutes());
    date.setSeconds(0);
    date.setMilliseconds(0);
    this._project[ propertyName ] = date;
  }

  setDates() {
    const now = new Date();
    const startDate = this._project.start_date ? new Date(this._project.start_date) : now;
    const endDate = this._project.end_date ? new Date(this._project.end_date) : now;
    this.setTimeInput(this.startTime.nativeElement, startDate);
    this.setTimeInput(this.endTime.nativeElement, endDate);
  }

  private setTimeInput(timeInput: HTMLInputElement, date: Date) {
    const d = new Date(0);
    d.setUTCHours(date.getHours());
    d.setUTCMinutes(date.getMinutes());
    timeInput.valueAsDate = d;
  }
}
