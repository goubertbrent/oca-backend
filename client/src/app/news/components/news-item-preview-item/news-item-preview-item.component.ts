import { ChangeDetectionStrategy, Component, Input, OnChanges, SimpleChanges } from '@angular/core';
import { BaseMedia, MediaType, NewsActionButton, NewsItemType } from '@oca/web-shared';
import { SharedService } from '../../../shared/shared.service';

@Component({
  selector: 'oca-news-item-preview-item',
  templateUrl: './news-item-preview-item.component.html',
  styleUrls: ['./news-item-preview-item.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class NewsItemPreviewItemComponent implements OnChanges {
  @Input() name: string;
  @Input() media?: BaseMedia | null;
  @Input() type: NewsItemType;
  @Input() qrCodeCaption?: string;
  @Input() avatarUrl: string;
  @Input() title: string;
  @Input() date: Date;
  @Input() message: string;
  @Input() actionButton: NewsActionButton | null;

  NewsItemType = NewsItemType;
  MediaType = MediaType;

  constructor(private sharedService: SharedService) {
  }

  ngOnChanges(changes: SimpleChanges): void {
    if (changes.media && changes.media.currentValue) {
      if (this.media && this.media.type === MediaType.VIDEO_YOUTUBE) {
        this.sharedService.ensureYoutubeLoaded();
      }
    }
  }
}
