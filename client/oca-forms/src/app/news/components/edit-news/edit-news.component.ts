import {
  ChangeDetectionStrategy,
  ChangeDetectorRef,
  Component,
  ElementRef,
  EventEmitter,
  Input,
  OnChanges,
  Output,
  SimpleChanges,
  ViewChild,
} from '@angular/core';
import { MatDialog, MatDialogConfig, MatSelectChange } from '@angular/material';
import { TranslateService } from '@ngx-translate/core';
import { UploadedFile } from '../../../shared/images';
import { Loadable } from '../../../shared/loadable/loadable';
import { UploadImageDialogComponent, UploadImageDialogConfig } from '../../../shared/upload-image-dialog/upload-image-dialog.component';
import {
  CreateNews,
  MediaType,
  NewsActionButton,
  NewsActionButtonType,
  NewsItemType,
  NewsOptions,
  UINewsActionButton,
} from '../../interfaces';

@Component({
  selector: 'oca-edit-news',
  templateUrl: './edit-news.component.html',
  styleUrls: [ './edit-news.component.scss' ],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class EditNewsComponent implements OnChanges {
  @ViewChild('scheduledTime') scheduledTime: ElementRef<HTMLInputElement>;

  @Input() set newsItem(value: CreateNews) {
    this._newsItem = value;
  };

  get newsItem() {
    return this._newsItem;
  }

  @Input() options: Loadable<NewsOptions>;
  @Input() actionButtons: Loadable<UINewsActionButton[]>;

  @Output() save = new EventEmitter<CreateNews>();
  NewsItemType = NewsItemType;
  scheduledDate: Date;
  minDate = new Date();

  actionButton: UINewsActionButton | null = null;
  NewsActionButtonType = NewsActionButtonType;

  private _newsItem: CreateNews;

  constructor(private _matDialog: MatDialog,
              private _translate: TranslateService,
              private _changeDetectorRef: ChangeDetectorRef) {

  }

  ngOnChanges(changes: SimpleChanges): void {
    if (this.actionButtons.data && this.newsItem && this.newsItem.action_button) {
      this.setActionButton(this.newsItem.action_button);
    }
    if (changes.newsItem && changes.newsItem.currentValue) {
      const news: CreateNews = changes.newsItem.currentValue;
      if (news.scheduled_at > 0) {
        this.scheduledDate = new Date(changes.newsItem.currentValue.scheduled_at * 1000);
      } else {
        this.scheduledDate = new Date();
      }
      this.updateDate();
      this.setTimeInput();
    }
  }

  showImageDialog() {
    const config: MatDialogConfig<UploadImageDialogConfig> = {
      data: {
        type: 'news',
        title: this._translate.instant('oca.image'),
      },
    };
    this._matDialog.open(UploadImageDialogComponent, config).afterClosed().subscribe((result?: UploadedFile) => {
      if (result) {
        this.newsItem = {
          ...this.newsItem,
          media: { type: MediaType.IMAGE, content: result.url },
        };
        this._changeDetectorRef.markForCheck();
      }
    });
  }

  actionButtonSelected(event: MatSelectChange) {
    if (this.actionButtons.data) {
      if (this.actionButton) {
        this.newsItem = { ...this.newsItem, action_button: this.actionButton.button };
      }
    }
  }

  compareActionButtons(toCompare: UINewsActionButton, selectedValue: UINewsActionButton | null) {
    if (!selectedValue) {
      return false;
    }
    return toCompare.type === selectedValue.type && toCompare.button.id === selectedValue.button.id;
  }

  setActionButton(button?: NewsActionButton) {
    if (!button) {
      this.actionButton = null;
      return;
    }
    if (this.actionButtons.data) {
      this.actionButton = this.actionButtons.data.find(b => b.button.id === button.id) || null;
      if (!this.actionButton) {
        return;
      }
      switch (this.actionButton.type) {
        case NewsActionButtonType.PHONE:
          this.actionButton.phone = button.action.split('tel://')[ 0 ];
          break;
        case NewsActionButtonType.EMAIL:
          this.actionButton.email = button.action.split('mailto://')[ 0 ];
          break;
        default:
          this.actionButton.button.action = button.action;
      }
    }
  }

  updateButton() {
    if (this.actionButton) {
      switch (this.actionButton.type) {
        case NewsActionButtonType.PHONE:
          this.actionButton.button.action = 'tel://' + this.actionButton.phone;
          break;
        case NewsActionButtonType.EMAIL:
          this.actionButton.button.action = 'mailto://' + this.actionButton.email;
          break;
      }
    }
  }

  toggleScheduledAt() {
    if (this.newsItem.scheduled_at) {
      this.newsItem = { ...this.newsItem, scheduled_at: 0 };
    } else {
      this.newsItem = { ...this.newsItem, scheduled_at: new Date().getTime() };
    }
  }

  updateDate() {
    let scheduledAt: Date | null = null;
    if (this.scheduledDate) {
      scheduledAt = new Date(this.scheduledDate.getTime());
      const timeDate = this.scheduledTime.nativeElement.valueAsDate as Date | undefined;
      if (timeDate) {
        scheduledAt.setHours(timeDate.getUTCHours());
        scheduledAt.setMinutes(timeDate.getUTCMinutes());
      }
    }
    this.newsItem.scheduled_at = scheduledAt ? scheduledAt.getTime() : 0;
  }

  private setTimeInput() {
    if (this.scheduledTime) {
      const d = new Date(0);
      d.setUTCHours(this.scheduledDate.getHours());
      d.setUTCMinutes(this.scheduledDate.getMinutes());
      this.scheduledTime.nativeElement.valueAsDate = d;
    }
  }
}
