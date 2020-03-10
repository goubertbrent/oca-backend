import { ChangeDetectionStrategy, Component, Input, OnChanges, SimpleChanges } from '@angular/core';
import { SafeResourceUrl } from '@angular/platform-browser';
import { SharedService } from '../../../shared/shared.service';
import { BaseMedia, MediaType, NewsActionButton, NewsItemType } from '../../interfaces';

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
  youtubeUrl: SafeResourceUrl | null = null;

  constructor(private sharedService: SharedService) {
  }

  ngOnChanges(changes: SimpleChanges): void {
    if (changes.media && changes.media.currentValue) {
      this.youtubeUrl = null;
      if (this.media && this.media.type === MediaType.YOUTUBE_VIDEO) {
        this.sharedService.ensureYoutubeLoaded();
      }
    }
  }
}
