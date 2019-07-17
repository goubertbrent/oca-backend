import { ChangeDetectionStrategy, Component, EventEmitter, Input, OnChanges, Output, SimpleChanges } from '@angular/core';
import { ServiceNewsGroup } from '../../../shared/interfaces/rogerthat';
import { NewsBroadcastItem } from '../../interfaces';

@Component({
  selector: 'oca-news-item-list',
  templateUrl: './news-item-list.component.html',
  styleUrls: [ './news-item-list.component.scss' ],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class NewsItemListComponent implements OnChanges {
  @Input() items: NewsBroadcastItem[];
  @Input() hasMore: boolean;
  @Input() loading: boolean;
  @Input() newsGroups: ServiceNewsGroup[];
  @Output() deleteItem = new EventEmitter<NewsBroadcastItem>();
  @Output() loadMore = new EventEmitter();

  newsGroupsMapping: { [ key: string ]: string } = {};

  ngOnChanges(changes: SimpleChanges): void {
    if (changes.newsGroups && this.newsGroups) {
      this.newsGroupsMapping = {};
      for (const group of this.newsGroups) {
        this.newsGroupsMapping[ group.group_type ] = group.name;
      }
    }
  }

  trackNews(index: number, item: NewsBroadcastItem) {
    return item.id;
  }
}
