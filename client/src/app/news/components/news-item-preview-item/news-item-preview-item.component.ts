import { ChangeDetectionStrategy, Component, Input } from '@angular/core';
import { BaseMedia, NewsActionButton, NewsItemType } from '../../interfaces';

@Component({
  selector: 'oca-news-item-preview-item',
  templateUrl: './news-item-preview-item.component.html',
  styleUrls: ['./news-item-preview-item.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class NewsItemPreviewItemComponent {
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
}
