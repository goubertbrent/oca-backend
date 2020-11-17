import { CdkDragDrop } from '@angular/cdk/drag-drop';
import { ChangeDetectionStrategy, Component, EventEmitter, Input, OnDestroy, Output } from '@angular/core';
import { FormArray, FormControl } from '@angular/forms';
import { MatDialog } from '@angular/material/dialog';
import { NEWS_GROUP_TYPES, SimpleDialogComponent, SimpleDialogData, SimpleDialogResult } from '@oca/web-shared';
import { IFormArray, IFormControl, IFormGroup } from '@rxweb/types';
import { ReplaySubject, Subject, Subscription } from 'rxjs';
import { takeUntil } from 'rxjs/operators';
import { moveItemInFormArray } from '../../../util';
import {
  BottomSheetListItemType,
  BottomSheetSectionTemplate,
  HomeScreenSectionType,
  ListSectionStyle,
  TranslationInternal, TranslationValue,
} from '../homescreen';
import { HomeScreenService } from '../home-screen.service';
import { HomeScreenBottomSheet, HomeScreenBottomSheetHeader } from '../models';

@Component({
  selector: 'rcc-home-screen-bottom-sheet',
  templateUrl: './home-screen-bottom-sheet.component.html',
  styleUrls: ['./home-screen-bottom-sheet.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class HomeScreenBottomSheetComponent implements OnDestroy {
  ROW_TEXT = HomeScreenSectionType.TEXT;
  ROW_LIST = HomeScreenSectionType.LIST;
  ROW_NEWS = HomeScreenSectionType.NEWS;
  listSectionStyles = [
    { value: ListSectionStyle.HORIZONTAL, label: 'Horizontal' },
    { value: ListSectionStyle.VERTICAL, label: 'Vertical' },
  ];
  rowTypes = [
    { value: HomeScreenSectionType.TEXT, label: 'Text' },
    { value: HomeScreenSectionType.LIST, label: 'List' },
    { value: HomeScreenSectionType.NEWS, label: 'News' },
  ];
  newsGroupTypes = NEWS_GROUP_TYPES;
  listItemTypes$: Subject<{ value: BottomSheetListItemType, label: string }[]> = new ReplaySubject();

  rowNames = this.rowTypes.reduce((acc, type) => {
    acc[ type.value ] = type.label;
    return acc;
  }, {} as { [key in HomeScreenSectionType]: string });

  @Input() formGroup: IFormGroup<HomeScreenBottomSheet>;
  @Input() translations: TranslationInternal[];
  @Input() translationsMapping : TranslationValue = {};
  @Output() addTranslation = new EventEmitter();

  editingRowType = new FormControl(HomeScreenSectionType.TEXT) as IFormControl<HomeScreenSectionType>;
  editingRow: IFormGroup<BottomSheetSectionTemplate>;
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
      let row: BottomSheetSectionTemplate;
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
        default:
          return;
      }
      this.editingRow = this.homeScreenFormsService.getHomeScreenItemForm(row);
      this.setupListItemTypes();
    });
  }

  get headerControls() {
    return (this.formGroup.controls.header as IFormGroup<HomeScreenBottomSheetHeader>).controls;
  }

  get rows(): IFormArray<BottomSheetSectionTemplate> {
    return this.formGroup.controls.rows as unknown as IFormArray<BottomSheetSectionTemplate>;
  }

  ngOnDestroy() {
    this.destroyed$.next();
    this.destroyed$.complete();
    this.listItemTypes$.complete();
  }

  addRow() {
    const row = this.homeScreenFormsService.getHomeScreenItemForm({ type: HomeScreenSectionType.TEXT, title: '', description: null });
    this.rows.push(row);
    this.editRow(row.value!!, this.rows.controls.length - 1);
  }

  editRow(row: BottomSheetSectionTemplate, index: number) {
    this.editingRowType.setValue(row.type, { emitEvent: false });
    this.editingRow = this.homeScreenFormsService.getHomeScreenItemForm(row);
    this.editingRowIndex = index;
    this.setupListItemTypes();
  }

  deleteRow(rowIndex: number) {
    const row = this.rows.at(rowIndex);
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
        this.rows.removeAt(rowIndex);
      }
    });
  }

  saveRow() {
    if (this.editingRow.valid) {
      this.rows.setControl(this.editingRowIndex, this.editingRow);
      this.editingRowIndex = -1;
    }
  }

  moveRow(event: CdkDragDrop<BottomSheetSectionTemplate>) {
    const array = this.rows as FormArray;
    moveItemInFormArray(array, event.previousIndex, event.currentIndex);
  }

  private setupListItemTypes() {
    this.setListItemTypes(this.editingRow.value);
    this.editingRowSubscription?.unsubscribe();
    this.editingRowSubscription = this.editingRow.valueChanges.pipe(takeUntil(this.destroyed$)).subscribe(editingRow => {
      this.setListItemTypes(editingRow);
    });
  }

  private setListItemTypes(row: BottomSheetSectionTemplate | null) {
    if (row?.type === HomeScreenSectionType.LIST) {
      this.listItemTypes$.next(this.possibleListItemTypes.filter(t => t.styles.includes(row.style)));
    }
  }
}
