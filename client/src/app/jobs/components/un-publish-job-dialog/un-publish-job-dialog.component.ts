import { ChangeDetectionStrategy, Component } from '@angular/core';
import { NgForm } from '@angular/forms';
import { MatDialogRef } from '@angular/material/dialog';
import { JOB_MATCH_SOURCES, JobMatched, JobMatchSource } from '../../jobs';

@Component({
  selector: 'oca-job-un-publish-dialog',
  templateUrl: './un-publish-job-dialog.component.html',
  styleUrls: ['./un-publish-job-dialog.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class UnPublishJobDialogComponent {
  sources = JOB_MATCH_SOURCES;
  SOURCE_EXTERN = JobMatchSource.EXTERN;
  jobMatch: JobMatched = {
    source: JobMatchSource.NO_MATCH,
    platform: null,
  };

  constructor(private matDialogRef: MatDialogRef<UnPublishJobDialogComponent>) {
  }

  submit(form: NgForm) {
    if (form.form.valid) {
      this.matDialogRef.close(this.jobMatch);
    }
  }
}
