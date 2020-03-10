import { CdkDragDrop, moveItemInArray } from '@angular/cdk/drag-drop';
import { ChangeDetectionStrategy, ChangeDetectorRef, Component, EventEmitter, Input, Output, ViewChild } from '@angular/core';
import { BaseMedia, MediaType } from '../../../news/interfaces';
import { MediaSelectorComponent } from '../../../shared/media-selector/media-selector/media-selector.component';
import { MapServiceMediaItem } from '../service-info';

@Component({
  selector: 'oca-service-media-editor',
  templateUrl: './service-media-editor.component.html',
  styleUrls: ['./service-media-editor.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class ServiceMediaEditorComponent {
  @ViewChild('mediaSelector') mediaSelector: MediaSelectorComponent;
  @Input() mediaItems: MapServiceMediaItem[];
  @Input() placeholderUrl?: string;
  @Output() mediaChanged = new EventEmitter<MapServiceMediaItem[]>();
  MediaType = MediaType;
  newMedia: BaseMedia | null = null;
  allowedMediaTypes = [MediaType.IMAGE];

  constructor(private changeDetectorRef: ChangeDetectorRef) {
  }

  addMediaItem(media: BaseMedia | null) {
    if (media) {
      this.mediaChanged.emit([...this.mediaItems, { role_ids: [], item: media }]);
      this.newMedia = null;
      this.changeDetectorRef.markForCheck();
    }
  }

  removeMedia(mediaItem: MapServiceMediaItem) {
    this.mediaChanged.emit(this.mediaItems.filter(m => m !== mediaItem));
  }

  itemDropped(event: CdkDragDrop<MapServiceMediaItem, any>) {
    moveItemInArray(this.mediaItems, event.previousIndex, event.currentIndex);
    this.mediaChanged.emit(this.mediaItems);
  }
}
