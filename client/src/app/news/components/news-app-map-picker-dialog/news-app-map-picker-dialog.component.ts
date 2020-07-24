import { ChangeDetectionStrategy, Component, Inject, ViewEncapsulation } from '@angular/core';
import { MAT_DIALOG_DATA, MatDialogRef } from '@angular/material/dialog';
import { App, AppStatisticsMapping } from '@oca/web-shared';

export interface NewsAppMapPickerDialogData {
  appIds: string[];
  apps: App[];
  appStatistics: AppStatisticsMapping;
  defaultAppId: string;
  mapUrl?: string | null;
}

@Component({
  selector: 'oca-news-app-map-picker-dialog',
  templateUrl: './news-app-map-picker-dialog.component.html',
  changeDetection: ChangeDetectionStrategy.OnPush,
  encapsulation: ViewEncapsulation.None,
})
export class NewsAppMapPickerDialogComponent {
  appIds: string[];
  apps: App[];
  appStatistics: AppStatisticsMapping;
  defaultAppId: string;
  mapUrl?: string | null;

  constructor(@Inject(MAT_DIALOG_DATA) private data: NewsAppMapPickerDialogData,
              private dialogRef: MatDialogRef<NewsAppMapPickerDialogComponent>) {
    this.appIds = data.appIds;
    this.apps = data.apps;
    this.appStatistics = data.appStatistics;
    this.defaultAppId = data.defaultAppId;
    this.mapUrl = data.mapUrl;
  }

  submit() {
    this.dialogRef.close(this.appIds);
  }

}
