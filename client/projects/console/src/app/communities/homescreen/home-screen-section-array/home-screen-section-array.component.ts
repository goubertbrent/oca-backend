import { CdkDragDrop } from '@angular/cdk/drag-drop';
import { ChangeDetectionStrategy, Component, EventEmitter, Input, OnDestroy, Output } from '@angular/core';
import { FormArray, FormControl } from '@angular/forms';
import { MatDialog } from '@angular/material/dialog';
import { NEWS_GROUP_TYPES, SimpleDialogComponent, SimpleDialogData, SimpleDialogResult } from '@oca/web-shared';
import { IFormArray, IFormControl, IFormGroup } from '@rxweb/types';
import { ReplaySubject, Subject, Subscription } from 'rxjs';
import { takeUntil } from 'rxjs/operators';
import { moveItemInFormArray } from '../../../util';
import { NewsGroup } from '../../news/news';
import { HomeScreenService } from '../home-screen.service';
import {
  BottomSheetListItemType,
  HomeScreenSectionTemplate,
  HomeScreenSectionType,
  ListSectionStyle,
  TranslationInternal,
  TranslationValue,
} from '../homescreen';

@Component({
  selector: 'rcc-home-screen-section-array',
  templateUrl: './home-screen-section-array.component.html',
  styleUrls: ['./home-screen-section-array.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class HomeScreenSectionArrayComponent implements OnDestroy {
  @Input() newsGroups: NewsGroup[];
  @Input() formArray: IFormArray<HomeScreenSectionTemplate>;
  @Input() translations: TranslationInternal[];
  @Input() translationsMapping: TranslationValue = {};
  @Output() addTranslation = new EventEmitter();

  ROW_TEXT = HomeScreenSectionType.TEXT;
  ROW_LIST = HomeScreenSectionType.LIST;
  ROW_NEWS = HomeScreenSectionType.NEWS;
  ROW_NEWS_ITEM = HomeScreenSectionType.NEWS_ITEM;
  listSectionStyles = [
    { value: ListSectionStyle.HORIZONTAL, label: 'Horizontal' },
    { value: ListSectionStyle.VERTICAL, label: 'Vertical' },
  ];
  rowTypes = [
    { value: HomeScreenSectionType.TEXT, label: 'Text' },
    { value: HomeScreenSectionType.LIST, label: 'List' },
    { value: HomeScreenSectionType.NEWS, label: 'News item list' },
    { value: HomeScreenSectionType.NEWS_ITEM, label: 'Featured news item' },
  ];
  newsGroupTypes = NEWS_GROUP_TYPES;
  listItemTypes$: Subject<{ value: BottomSheetListItemType, label: string }[]> = new ReplaySubject();

  rowNames = this.rowTypes.reduce((acc, type) => {
    acc[ type.value ] = type.label;
    return acc;
  }, {} as { [key in HomeScreenSectionType]: string });

  editingRowType = new FormControl(HomeScreenSectionType.TEXT) as IFormControl<HomeScreenSectionType>;
  editingRow: IFormGroup<HomeScreenSectionTemplate>;
  editingRowIndex = -1;

  private destroyed$ = new Subject();
  private possibleListItemTypes = [
    { styles: [ListSectionStyle.VERTICAL], value: BottomSheetListItemType.EXPANDABLE, label: 'Expandable' },
    { styles: [ListSectionStyle.VERTICAL, ListSectionStyle.HORIZONTAL], value: BottomSheetListItemType.LINK, label: 'Button' },
    { styles: [ListSectionStyle.VERTICAL], value: BottomSheetListItemType.OPENING_HOURS, label: 'Opening hours' },
  ];
  private editingRowSubscription: Subscription;

  constructor(private homeScreenFormsService: HomeScreenService,
              private matDialog: MatDialog) {
    this.editingRowType.valueChanges.pipe(takeUntil(this.destroyed$)).subscribe(type => {
      let row: HomeScreenSectionTemplate;
      switch (type) {
        case HomeScreenSectionType.TEXT:
          row = { type, description: null, title: '' };
          break;
        case HomeScreenSectionType.LIST:
          row = { type, items: [], style: ListSectionStyle.VERTICAL };
          break;
        case HomeScreenSectionType.NEWS:
          row = {
            type,
            filter: { service_identity_email: null, search_string: null, group_type: null, group_id: null },
            limit: 5,
          };
          break;
        case HomeScreenSectionType.NEWS_ITEM:
          row = {
            type,
            group_id: '',
          };
          break;
        default:
          return;
      }
      this.editingRow = this.homeScreenFormsService.getHomeScreenItemForm(row);
      this.setupListItemTypes();
    });
  }

  ngOnDestroy() {
    this.destroyed$.next();
    this.destroyed$.complete();
    this.listItemTypes$.complete();
  }

  addRow() {
    const row = this.homeScreenFormsService.getHomeScreenItemForm({ type: HomeScreenSectionType.TEXT, title: '', description: null });
    this.formArray.push(row);
    this.editRow(row.value!!, this.formArray.controls.length - 1);
  }

  editRow(row: HomeScreenSectionTemplate, index: number) {
    this.editingRowType.setValue(row.type, { emitEvent: false });
    this.editingRow = this.homeScreenFormsService.getHomeScreenItemForm(row);
    this.editingRowIndex = index;
    this.setupListItemTypes();
  }

  deleteRow(rowIndex: number) {
    const row = this.formArray.at(rowIndex);
    const rowName = this.rowNames[ row.value!.type ];
    const data: SimpleDialogData = {
      title: 'Confirmation',
      message: `Are you sure you want to delete this ${rowName} row?`,
      ok: 'Yes',
      cancel: 'No',
    };
    this.matDialog.open<SimpleDialogComponent, SimpleDialogData, SimpleDialogResult>(SimpleDialogComponent, { data })
      .afterClosed().subscribe(result => {
      if (result?.submitted) {
        this.formArray.removeAt(rowIndex);
      }
    });
  }

  saveRow() {
    if (this.editingRow.valid) {
      this.formArray.setControl(this.editingRowIndex, this.editingRow);
      this.editingRowIndex = -1;
    }
  }

  moveRow(event: CdkDragDrop<HomeScreenSectionTemplate>) {
    moveItemInFormArray(this.formArray as FormArray, event.previousIndex, event.currentIndex);
  }

  private setupListItemTypes() {
    this.setListItemTypes(this.editingRow.value);
    this.editingRowSubscription?.unsubscribe();
    this.editingRowSubscription = this.editingRow.valueChanges.pipe(takeUntil(this.destroyed$)).subscribe(editingRow => {
      this.setListItemTypes(editingRow);
    });
  }

  private setListItemTypes(row: HomeScreenSectionTemplate | null) {
    if (row?.type === HomeScreenSectionType.LIST) {
      this.listItemTypes$.next(this.possibleListItemTypes.filter(t => t.styles.includes(row.style)));
    }
  }
}
