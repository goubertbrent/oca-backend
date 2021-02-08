import { HttpClient } from '@angular/common/http';
import { ChangeDetectionStrategy, Component, OnInit } from '@angular/core';
import { FormControl, FormGroup, Validators } from '@angular/forms';
import { ErrorService } from '@oca/web-shared';
import { Subject } from 'rxjs';

interface TimeblockrSettings {
  url: string;
  api_key: string;
}

@Component({
  selector: 'oca-timeblockr-settings-page',
  templateUrl: './timeblockr-settings-page.component.html',
  styleUrls: ['./timeblockr-settings-page.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class TimeblockrSettingsPageComponent implements OnInit {
  formGroup = new FormGroup({
    url: new FormControl(null, Validators.required),
    api_key: new FormControl(null, Validators.required),
  });
  loading$ = new Subject<boolean>();

  constructor(private http: HttpClient,
              private errorService: ErrorService) {
  }

  ngOnInit(): void {
    this.http.get<TimeblockrSettings>('/common/timeblockr').subscribe(result => {
      if (result) {
        this.formGroup.patchValue(result);
      }
    });
    this.loading$.subscribe(loading => {
      if (loading) {
        this.formGroup.disable();
      } else {
        this.formGroup.enable();
      }
    });
  }

  saveSettings() {
    if (this.formGroup.valid) {
      this.loading$.next(true);
      this.http.put<TimeblockrSettings>('/common/timeblockr', this.formGroup.value).subscribe(() => {
        this.loading$.next(false);
      }, err => {
        this.loading$.next(false);
        const msg = this.errorService.getMessage(err);
        this.errorService.showErrorDialog(msg);
      });
    }
  }

}
