import { ChangeDetectionStrategy, Component, Inject } from '@angular/core';
import { NgForm } from '@angular/forms';
import { MAT_DIALOG_DATA, MatDialogRef } from '@angular/material/dialog';

export type  PublishJobDialogResult =
  { publishNow: true } |
  { publishNow: false; date: Date; };

@Component({
  selector: 'oca-publish-job-dialog',
  templateUrl: './publish-job-dialog.component.html',
  styleUrls: ['./publish-job-dialog.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class PublishJobDialogComponent {
  minDate = new Date();
  selectedValue: 'now' | 'scheduled' = 'now';
  date: Date | null = null;
  datePickerOpened = false;

  constructor(private matDialogRef: MatDialogRef<PublishJobDialogComponent>,
              @Inject(MAT_DIALOG_DATA) private data: { date: Date | null }) {
    this.minDate.setDate(this.minDate.getDate() + 1);
    this.date = data.date;
    if (this.date) {
      this.selectedValue = 'scheduled';
    } else {
      this.datePickerOpened = true;
    }
  }

  submit(form: NgForm) {
    if (form.form.valid) {
      const publishNow = this.selectedValue === 'now';
      const result: PublishJobDialogResult = publishNow ? { publishNow } : { publishNow, date: this.date as Date };
      this.matDialogRef.close(result);
    } else {
      form.form.controls.date.markAsTouched();
      form.form.controls.date.markAsDirty();
    }
  }
}
