import { ChangeDetectionStrategy, Component, Input } from '@angular/core';
import { CreateNews, NewsItemType } from '../../interfaces';

@Component({
  selector: 'oca-news-item-preview',
  templateUrl: './news-item-preview.component.html',
  styleUrls: [ './news-item-preview.component.scss' ],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class NewsItemPreviewComponent {
  NewsItemType = NewsItemType;
  @Input() newsItem: CreateNews;
  @Input() name: string;
  @Input() date: Date = new Date();
}
