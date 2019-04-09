import { ChangeDetectionStrategy, Component, EventEmitter, Input, Output } from '@angular/core';
import { NewsBroadcastItem } from '../../interfaces';

@Component({
  selector: 'oca-news-item-list',
  templateUrl: './news-item-list.component.html',
  styleUrls: [ './news-item-list.component.scss' ],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class NewsItemListComponent {
  @Input() items: NewsBroadcastItem[];
  @Input() hasMore: boolean;
  @Output() deleteItem = new EventEmitter<NewsBroadcastItem>();
  @Output() loadMore = new EventEmitter();

  trackNews(index: number, item: NewsBroadcastItem) {
    return item.id;
  }
}
