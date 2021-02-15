import { ChangeDetectionStrategy, Component, Inject, OnDestroy } from '@angular/core';
import { FormBuilder, FormControl, Validators } from '@angular/forms';
import { MAT_DIALOG_DATA, MatDialogRef } from '@angular/material/dialog';
import { select, Store } from '@ngrx/store';
import { IFormBuilder, IFormGroup } from '@rxweb/types';
import { Observable, Subject } from 'rxjs';
import { debounceTime, takeUntil } from 'rxjs/operators';
import { NewsFeaturedItem, NewsGroupFeaturedItemType, NewsListItem, SetFeaturedItemData } from '../../news';
import { GetNewsListAction } from '../../news.actions';
import { getNewsItems, isNewsListLoading } from '../../news.state';

@Component({
  selector: 'oca-edit-featured-item-dialog',
  templateUrl: './edit-featured-item-dialog.component.html',
  styleUrls: ['./edit-featured-item-dialog.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class EditFeaturedItemDialogComponent implements OnDestroy {
  typeOptions = [
    { value: NewsGroupFeaturedItemType.NONE, label: 'oca.no_featured_news_item' },
    { value: NewsGroupFeaturedItemType.SPECIFIC_ITEM, label: 'oca.specific_message' },
    { value: NewsGroupFeaturedItemType.LAST_ITEM, label: 'oca.last_published_news_item' },
  ];
  SPECIFIC_ITEM = NewsGroupFeaturedItemType.SPECIFIC_ITEM;
  formGroup: IFormGroup<Omit<SetFeaturedItemData, 'group_id'>>;
  newsSearchControl = new FormControl();
  fb: IFormBuilder;
  newsItems$: Observable<NewsListItem[]>;
  loadingNewsItems$: Observable<boolean>;

  private destroyed$ = new Subject();

  constructor(@Inject(MAT_DIALOG_DATA) public data: NewsFeaturedItem,
              fb: FormBuilder,
              private store: Store,
              private matDialogRef: MatDialogRef<EditFeaturedItemDialogComponent>) {
    this.fb = fb as IFormBuilder;
    this.formGroup = this.fb.group<Omit<SetFeaturedItemData, 'group_id'>>({
      news_id: this.fb.control(data.item?.id ?? null),
      type: this.fb.control(data.type, Validators.required),
    });
    this.formGroup.controls.type.valueChanges.pipe(takeUntil(this.destroyed$)).subscribe(type => {
      this.formGroup.controls.news_id.setValidators(type === NewsGroupFeaturedItemType.SPECIFIC_ITEM ? Validators.required : []);
      this.formGroup.controls.news_id.updateValueAndValidity();
    });
    this.newsItems$ = this.store.pipe(select(getNewsItems));
    this.loadingNewsItems$ = this.store.pipe(select(isNewsListLoading));
    this.newsSearchControl.valueChanges.pipe(takeUntil(this.destroyed$), debounceTime(600)).subscribe(searchText => {
      // Currently this is not limited by news group, but let's call that a feature instead of an oversight
      this.store.dispatch(new GetNewsListAction({ query: searchText, cursor: null, amount: 5 }));
    });
  }

  ngOnDestroy() {
    this.destroyed$.next();
    this.destroyed$.complete();
  }

  setSelectedItem(newsItem: NewsListItem) {
    this.formGroup.controls.news_id.setValue(newsItem.id);
    this.data.item = { id: newsItem.id, title: newsItem.title, timestamp: newsItem.timestamp };
  }

  save() {
    const value = this.formGroup.value!;
    console.log(this.formGroup);
    if (this.formGroup.valid) {
      const result: SetFeaturedItemData = { group_id: this.data.group.id, ...value };
      this.matDialogRef.close(result);
    }
  }
}
