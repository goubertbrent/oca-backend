import { ChangeDetectionStrategy, Component, Inject, ViewEncapsulation } from '@angular/core';
import { MAT_DIALOG_DATA, MatDialogRef } from '@angular/material/dialog';
import { NewsCommunityMapping } from '../../news';

export interface NewsAppMapPickerDialogData {
  selectedCommunityIds: number[];
  communityMapping: NewsCommunityMapping;
  defaultCommunity: number;
  mapUrl?: string | null;
}

@Component({
  selector: 'oca-news-app-map-picker-dialog',
  templateUrl: './news-app-map-picker-dialog.component.html',
  changeDetection: ChangeDetectionStrategy.OnPush,
  encapsulation: ViewEncapsulation.None,
})
export class NewsAppMapPickerDialogComponent {
  selectedCommunities: number[];
  communityMapping: NewsCommunityMapping;
  defaultCommunityId: number;
  mapUrl?: string | null;

  constructor(@Inject(MAT_DIALOG_DATA) private data: NewsAppMapPickerDialogData,
              private dialogRef: MatDialogRef<NewsAppMapPickerDialogComponent>) {
    this.selectedCommunities = data.selectedCommunityIds;
    this.communityMapping = data.communityMapping;
    this.defaultCommunityId = data.defaultCommunity;
    this.mapUrl = data.mapUrl;
  }

  submit() {
    this.dialogRef.close(this.selectedCommunities);
  }

}
