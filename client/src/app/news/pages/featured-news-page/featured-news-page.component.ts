import { ChangeDetectionStrategy, Component, OnInit } from '@angular/core';
import { MatDialog } from '@angular/material/dialog';
import { select, Store } from '@ngrx/store';
import { Observable } from 'rxjs';
import { EditFeaturedItemDialogComponent } from '../../components/edit-featured-item-dialog/edit-featured-item-dialog.component';
import { NewsFeaturedItem, NewsGroupFeaturedItemType, SetFeaturedItemData } from '../../news';
import { LoadFeaturedItems, SetFeaturedItem } from '../../news.actions';
import { getFeaturedItems } from '../../news.state';

@Component({
  selector: 'oca-featured-news-page',
  templateUrl: './featured-news-page.component.html',
  styleUrls: ['./featured-news-page.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class FeaturedNewsPageComponent implements OnInit {
  featuredItems$: Observable<NewsFeaturedItem[]>;
  NONE_TYPE = NewsGroupFeaturedItemType.NONE;
  SPECIFIC_ITEM_TYPE = NewsGroupFeaturedItemType.SPECIFIC_ITEM;
  LAST_ITEM_TYPE = NewsGroupFeaturedItemType.LAST_ITEM;

  constructor(private store: Store,
              private matDialog: MatDialog) {
  }

  ngOnInit() {
    this.store.dispatch(new LoadFeaturedItems());
    this.featuredItems$ = this.store.pipe(select(getFeaturedItems));
  }

  editFeaturedItem(item: NewsFeaturedItem) {
    this.matDialog.open<EditFeaturedItemDialogComponent, NewsFeaturedItem, SetFeaturedItemData>(EditFeaturedItemDialogComponent,
      { data: item }).afterClosed().subscribe(result => {
      if (result) {
        this.store.dispatch(new SetFeaturedItem(result));
      }
    });
  }
}
