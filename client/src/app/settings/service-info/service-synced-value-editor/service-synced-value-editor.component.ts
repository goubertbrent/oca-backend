import { CdkDragDrop, moveItemInArray } from '@angular/cdk/drag-drop';
import { ChangeDetectionStrategy, Component, EventEmitter, Input, Output, ViewChild } from '@angular/core';
import { NgModel } from '@angular/forms';
import { TranslateService } from '@ngx-translate/core';
import { SyncedNameValue } from '../service-info';

@Component({
  selector: 'oca-service-value-editor',
  templateUrl: './service-synced-value-editor.component.html',
  styleUrls: ['./service-synced-value-editor.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class ServiceSyncedValueEditorComponent {
  @ViewChild('inputFieldModel', { static: false }) inputFieldModel: NgModel;
  @Input() values: SyncedNameValue[];
  @Input() valueLabel: string;
  @Input() inputType: string;
  @Input() maxCount = 3;
  @Output() valueChanged = new EventEmitter<SyncedNameValue[]>();
  editingIndex: number | null = null;
  editingValue: SyncedNameValue | null = null;
  NEW_ITEM_INDEX = -1;
  syncedMessage: string;

  constructor(private translate: TranslateService) {
    this.syncedMessage = this.translate.instant('oca.value_synced_via_paddle_cannot_edit');
  }

  changed() {
    this.valueChanged.emit(this.values);
  }

  removeValue(value: SyncedNameValue) {
    this.values = this.values.filter(v => v !== value);
    this.changed();
  }

  saveValue() {
    if (!this.editingValue || !(this.editingValue.value || '').trim()) {
      const control = this.inputFieldModel.control;
      control.markAsTouched();
      control.markAsDirty();
      control.updateValueAndValidity();
      return;
    }
    if (this.editingIndex === this.NEW_ITEM_INDEX) {
      this.values.push(this.editingValue);
    } else {
      this.values[ this.editingIndex as number ] = this.editingValue;
    }
    this.editingIndex = null;
    this.editingValue = null;
    this.changed();
  }

  addValue() {
    this.editingValue = { value: '', name: null };
    this.editingIndex = this.NEW_ITEM_INDEX;
  }

  editValue(value: SyncedNameValue) {
    this.editingValue = { ...value };
    this.editingIndex = this.values.indexOf(value);
  }

  itemMoved($event: CdkDragDrop<any>) {
    moveItemInArray(this.values, $event.previousIndex, $event.currentIndex);
  }
}
