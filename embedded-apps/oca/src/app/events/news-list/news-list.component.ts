import { ChangeDetectionStrategy, Component, EventEmitter, Input, Output } from '@angular/core';
import { NewsStreamItem } from '../../rogerthat';

@Component({
  selector: 'app-news-list',
  templateUrl: './news-list.component.html',
  styleUrls: ['./news-list.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class NewsListComponent {
  @Input() newsItems: NewsStreamItem[];
  @Input() loading: boolean;
  @Output() itemClicked = new EventEmitter<NewsStreamItem>();

  placeholders = [1, 2, 3];
}
