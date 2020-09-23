import { ChangeDetectionStrategy, Component, Input } from '@angular/core';
import { NewsItemType } from '@oca/web-shared';
import { CreateNews } from '../../news';

@Component({
  selector: 'oca-news-item-preview',
  templateUrl: './news-item-preview.component.html',
  styleUrls: ['./news-item-preview.component.scss'],
  changeDetection: ChangeDetectionStrategy.Default,
})
export class NewsItemPreviewComponent {
  NewsItemType = NewsItemType;
  @Input() newsItem: CreateNews;
  @Input() name: string;
  @Input() avatarUrl: string;

  private _date = new Date();

  get date() {
    return this._date;
  }

  @Input() set date(value: Date | null) {
    this._date = value || new Date();
  }
}
