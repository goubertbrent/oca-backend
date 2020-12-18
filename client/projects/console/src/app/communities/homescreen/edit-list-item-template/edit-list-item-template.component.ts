import { CdkDragDrop } from '@angular/cdk/drag-drop';
import { ChangeDetectionStrategy, Component, EventEmitter, Input, OnChanges, OnDestroy, Output, SimpleChanges } from '@angular/core';
import { FormArray, FormControl, Validators } from '@angular/forms';
import { IFormArray, IFormControl, IFormGroup } from '@rxweb/types';
import { Subject } from 'rxjs';
import { takeUntil } from 'rxjs/operators';
import { moveItemInFormArray } from '../../../util';
import {
  BottomSheetListItemTemplate,
  BottomSheetListItemType,
  ExpandableItemSource,
  LinkItemSource,
  LinkListItemStyle,
  TranslationInternal, TranslationValue,
} from '../homescreen';
import { HomeScreenService } from '../home-screen.service';

@Component({
  selector: 'rcc-edit-list-item-template',
  templateUrl: './edit-list-item-template.component.html',
  styleUrls: ['./edit-list-item-template.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class EditListItemTemplateComponent implements OnDestroy, OnChanges {
  itemTypeLabels: { [key in BottomSheetListItemType]?: string } = {};
  expandableSources = [
    { value: ExpandableItemSource.NONE, label: 'None' },
    { value: ExpandableItemSource.SERVICE_INFO_DESCRIPTION, label: 'Service description' },
  ];
  buttonStyles = [
    { value: LinkListItemStyle.ROUND_BUTTON_WITH_ICON, label: 'Round button' },
    { value: LinkListItemStyle.BUTTON, label: 'Block button' },
  ];
  EXPANDABLE_SOURCE_NONE = ExpandableItemSource.NONE;
  EXPANDABLE_ITEM = BottomSheetListItemType.EXPANDABLE;
  LINK_ITEM = BottomSheetListItemType.LINK;

  @Input() formArray: IFormArray<BottomSheetListItemTemplate>;
  @Input() itemTypes: { value: BottomSheetListItemType, label: string }[] = [];
  @Input() translations: TranslationInternal[];
  @Input() translationsMapping: TranslationValue;
  @Output() addTranslation = new EventEmitter();

  editingTypeControl = new FormControl(BottomSheetListItemType.EXPANDABLE, Validators.required) as IFormControl<BottomSheetListItemType>;
  editingFormGroup: IFormGroup<BottomSheetListItemTemplate>;
  editingIndex = -1;

  private destroyed$ = new Subject();

  constructor(private formService: HomeScreenService) {
    this.editingTypeControl.valueChanges.pipe(takeUntil(this.destroyed$)).subscribe(type => {
      let row: BottomSheetListItemTemplate;
      switch (type) {
        case BottomSheetListItemType.OPENING_HOURS:
          row = { type };
          break;
        case BottomSheetListItemType.EXPANDABLE:
          row = { type, source: ExpandableItemSource.NONE, icon: null, title: null };
          break;
        case BottomSheetListItemType.LINK:
          row = {
            type,
            style: LinkListItemStyle.ROUND_BUTTON_WITH_ICON,
            title: null,
            icon_color: null,
            content: { source: LinkItemSource.SERVICE_INFO_PHONE, index: 0 },
            icon: null,
          };
          break;
        default:
          return;
      }
      this.editingFormGroup = this.formService.getListItemForm(row);
    });
  }

  ngOnChanges(changes: SimpleChanges) {
    if (changes.itemTypes?.currentValue) {
      this.itemTypeLabels = this.itemTypes.reduce((acc, type) => {
        acc[ type.value ] = type.label;
        return acc;
      }, {} as { [key in BottomSheetListItemType]: string });
    }
  }

  ngOnDestroy() {
    this.destroyed$.next();
    this.destroyed$.complete();
  }

  addItem() {
    const item: BottomSheetListItemTemplate = {
      type: BottomSheetListItemType.EXPANDABLE,
      title: null,
      icon: null,
      source: ExpandableItemSource.NONE,
    };
    this.formArray.push(this.formService.getListItemForm(item));
    this.editItem(item, this.formArray.value.length - 1);
  }

  editItem(value: BottomSheetListItemTemplate, index: number) {
    this.editingFormGroup = this.formService.getListItemForm(value);
    this.editingIndex = index;
    this.editingTypeControl.setValue(value.type, { emitEvent: false });
  }

  deleteItem(index: number) {
    this.formArray.removeAt(index);
  }

  saveItem() {
    if (this.editingFormGroup.valid) {
      this.formArray.setControl(this.editingIndex, this.editingFormGroup);
      this.editingIndex = -1;
    }
  }

  moveItem($event: CdkDragDrop<BottomSheetListItemTemplate>) {
    moveItemInFormArray(this.formArray as FormArray, $event.previousIndex, $event.currentIndex);
  }
}
