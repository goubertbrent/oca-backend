import { ChangeDetectionStrategy, Component, EventEmitter, Input, Output } from '@angular/core';
import { TranslateService } from '@ngx-translate/core';
import { DialogService } from '../../../../../framework/client/dialog';
import { AppNavigationItem, AppNavigationItemError, BuildSettings } from '../../../interfaces';
import { EditNavigationItemDialogComponent } from './edit-navigation-item-dialog.component';

@Component({
  selector: 'rcc-navigation-item-list',
  changeDetection: ChangeDetectionStrategy.OnPush,
  templateUrl: 'navigation-item-list.component.html',
  styles: [ `mat-icon[mat-list-avatar] {
    font-size: 36px;
    text-align: center;
    background: none;
  }` ],
})
export class NavigationItemListComponent {
  @Input() value: AppNavigationItem[];
  @Input() color: string;
  @Input() maxCount?: number;
  @Input() errors: AppNavigationItemError[];
  @Input() buildSettings: BuildSettings;

  @Output() update = new EventEmitter<AppNavigationItem[]>();

  constructor(private translate: TranslateService,
              private dialogService: DialogService) {
  }

  trackByIndex(index: number, item: AppNavigationItem) {
    return index;
  }

  getErrorMessage(index: number) {
    if (this.errors && this.errors[ index ]) {
      for (const property in this.errors[ index ]) {
        if (this.errors[ index ].hasOwnProperty(property)) {
          return `${this.translate.instant('rcc.' + property)}: ${this.errors[ index ][ property ]}`;
        }
      }
    }
    return null;
  }

  edit(item: AppNavigationItem) {
    const options = {
      data: {
        item: item,
        customTranslations: this.buildSettings ? this.buildSettings.translations : {},
      },
    };
    const sub = this.dialogService.open(EditNavigationItemDialogComponent, options).afterClosed().subscribe((updatedItem: AppNavigationItem | undefined) => {
      if (updatedItem) {
        let index = 0;
        this.value = this.value.map((i: AppNavigationItem) => {
          if (i === item) {
            index = this.value.indexOf(i);
          }
          return i;
        });
        this.value.splice(index, 1, updatedItem);
        this.update.emit(this.value);
      }
      sub.unsubscribe();
    });
  }

  remove(item: AppNavigationItem) {
    const config = {
      title: this.translate.instant('rcc.confirmation'),
      message: this.translate.instant('rcc.confirm_delete_navigation_item'),
      ok: this.translate.instant('rcc.ok'),
      cancel: this.translate.instant('rcc.cancel'),
    };
    const sub = this.dialogService.openConfirm(config).afterClosed().subscribe((confirmed: boolean) => {
      if (confirmed) {
        this.value = [ ...this.value.filter(i => i !== item) ];
        this.update.emit(this.value);
      }
      sub.unsubscribe();
    });
  }

  add() {
    const options = {
      data: {
        item: <AppNavigationItem>{
          action: null,
          action_type: '',
          color: null,
          icon: '',
          text: '',
          params: {},
        },
      },
    };
    const sub = this.dialogService.open(EditNavigationItemDialogComponent, options).afterClosed().subscribe((newItem: AppNavigationItem | undefined) => {
      if (newItem) {
        this.value = [ ...this.value, newItem ];
        this.update.emit(this.value);
      }
      sub.unsubscribe();
    });
  }

  move(item: AppNavigationItem, up: boolean) {
    const index = this.value.indexOf(item);
    const newIndex = up ? index - 1 : index + 1;
    this.value.splice(index, 0, this.value.splice(newIndex, 1)[ 0 ]);
  }
}
