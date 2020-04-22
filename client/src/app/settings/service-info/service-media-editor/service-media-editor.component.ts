import { CdkDragDrop, moveItemInArray } from '@angular/cdk/drag-drop';
import { ChangeDetectionStrategy, ChangeDetectorRef, Component, forwardRef, Input, ViewChild } from '@angular/core';
import { ControlValueAccessor, NG_VALUE_ACCESSOR } from '@angular/forms';
import { BaseMedia, MediaType } from '../../../news/interfaces';
import { MediaSelectorComponent } from '../../../shared/media-selector/media-selector/media-selector.component';
import { MapServiceMediaItem } from '../service-info';

@Component({
  selector: 'oca-service-media-editor',
  templateUrl: './service-media-editor.component.html',
  styleUrls: ['./service-media-editor.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush, providers: [{
    provide: NG_VALUE_ACCESSOR,
    useExisting: forwardRef(() => ServiceMediaEditorComponent),
    multi: true,
  }],
})
export class ServiceMediaEditorComponent implements ControlValueAccessor {
  @ViewChild('mediaSelector') mediaSelector: MediaSelectorComponent;
  @Input() placeholderUrl?: string;
  mediaItems: MapServiceMediaItem[];

  disabled = false;
  MediaType = MediaType;
  newMedia: BaseMedia | null = null;
  allowedMediaTypes = [MediaType.IMAGE];

  constructor(private changeDetectorRef: ChangeDetectorRef) {
  }

  addMediaItem(media: BaseMedia | null) {
    if (media) {
      this.mediaItems = [...this.mediaItems, { role_ids: [], item: media }];
      this.onChange(this.mediaItems);
      this.newMedia = null;
    }
  }

  removeMedia(mediaItem: MapServiceMediaItem) {
    this.mediaItems = this.mediaItems.filter(m => m !== mediaItem);
    this.onChange(this.mediaItems);
  }

  itemDropped(event: CdkDragDrop<MapServiceMediaItem, any>) {
    moveItemInArray(this.mediaItems, event.previousIndex, event.currentIndex);
    this.onChange(this.mediaItems);
  }

  registerOnChange(fn: any): void {
    this.onChange = fn;
  }

  registerOnTouched(fn: any): void {
    this.onTouched = fn;
  }

  setDisabledState(isDisabled: boolean): void {
    this.disabled = isDisabled;
    this.changeDetectorRef.markForCheck();
  }

  writeValue(values?: MapServiceMediaItem[]): void {
    if (values) {
      this.mediaItems = values;
      this.changeDetectorRef.markForCheck();
    }
  }

  private onChange = (_: any) => {
  };
  private onTouched = () => {
  };
}
