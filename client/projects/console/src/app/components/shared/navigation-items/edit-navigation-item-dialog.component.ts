import { ChangeDetectionStrategy, Component, Inject, OnInit, ViewChild } from '@angular/core';
import { FormControl, Validators } from '@angular/forms';
import { MatAutocomplete } from '@angular/material/autocomplete';
import { MAT_DIALOG_DATA, MatDialogRef } from '@angular/material/dialog';
import { Observable } from 'rxjs';
import { auditTime, map } from 'rxjs/operators';
import {
  COLLAPSE_NAVIGATION_ACTIONS,
  filterIcons,
  FontAwesomeIcon,
  HARDCODED_ICONS,
  iconValidator,
  NAVIGATION_ACTION_TRANSLATIONS,
  NAVIGATION_ACTION_TYPES,
  NAVIGATION_ACTIONS,
} from '../../../constants';
import { AppNavigationItem, NavigationAction, Translations } from '../../../interfaces';

export interface EditNavigationItemDialogData {
  item: AppNavigationItem;
  customTranslations: Translations;
}

@Component({
  selector: 'rcc-edit-navigation-item-dialog',
  changeDetection: ChangeDetectionStrategy.OnPush,
  templateUrl: 'edit-navigation-item-dialog.component.html',
})
export class EditNavigationItemDialogComponent implements OnInit {
  @ViewChild('actionTypeComplete', { static: true }) actionTypeComplete: MatAutocomplete;
  @ViewChild('textComplete', { static: true }) textComplete: MatAutocomplete;
  @ViewChild('iconComplete', { static: true }) iconComplete: MatAutocomplete;

  NAVIGATION_ACTION_TYPES = NAVIGATION_ACTION_TYPES;
  HARDCODED_ICONS = HARDCODED_ICONS;
  navigationItem: AppNavigationItem;
  useGlobalColor: boolean;
  textControl: FormControl;
  iconControl: FormControl;
  actionTypeControl: FormControl;
  filteredText: Observable<string[]>;
  filteredIcons: Observable<FontAwesomeIcon[]>;
  filteredActionTypes: Observable<NavigationAction[]>;
  chosenIcon: string;

  private translations: string[] = NAVIGATION_ACTION_TRANSLATIONS;

  constructor(private dialogRef: MatDialogRef<EditNavigationItemDialogComponent>,
              @Inject(MAT_DIALOG_DATA) private data: EditNavigationItemDialogData) {
  }

  ngOnInit() {
    this.navigationItem = { ...this.data.item };
    this.textControl = new FormControl(this.navigationItem.text, [Validators.required]);
    this.iconControl = new FormControl(this.navigationItem.icon, [Validators.required, iconValidator]);
    this.actionTypeControl = new FormControl(this.navigationItem.action_type, [Validators.required]);
    this.filteredText = this.textControl.valueChanges.pipe(map(text => this.filterText(text)));
    this.filteredIcons = this.iconControl.valueChanges.pipe(auditTime(300), map(text => Array.from(filterIcons(text))));
    this.filteredActionTypes = this.actionTypeControl.valueChanges.pipe(map(text => this.filterActionTypes(text)));
    this.useGlobalColor = !this.navigationItem.color;
    this.chosenIcon = this.navigationItem.icon;
    if (this.data.customTranslations && 'en' in this.data.customTranslations) {
      this.translations = this.translations.concat(this.data.customTranslations.en.map(t => t.value));
    }
  }

  useGlobalColorChanged(useGlobalColor: boolean) {
    if (!useGlobalColor) {
      this.navigationItem.color = '#000';
    }
  }

  actionChanged() {
    if (!(this.isCollapsible())) {
      delete this.navigationItem.params.collapse;
    }
  }

  isCollapsible(): boolean {
    return COLLAPSE_NAVIGATION_ACTIONS.includes(this.navigationItem.action as string);
  }

  isOpenApp(): boolean {
    return this.navigationItem.action_type === 'open' &&
      this.navigationItem.action === 'app';
  }

  getIcon() {
    this.navigationItem.icon = (this.navigationItem.icon || '').replace(/ /g, '');
    return this.navigationItem.icon;
  }

  cancel() {
    this.dialogRef.close();
  }

  submit() {
    this.dialogRef.close(this.navigationItem);
  }

  private filterText(text: string) {
    if (!text) {
      return this.translations;
    }
    return this.translations.filter(t => new RegExp(text, 'gi').test(t));
  }

  private filterActionTypes(text: string) {
    // Could improve this by doing API calls to rogerthat and suggesting menu items of the main service in case
    // action_type is 'click'
    // For action_type 'action' we could do another api call for action_type 'action'
    // by getting the available tags or something.
    return NAVIGATION_ACTIONS.filter(action => {
      const isSameActionType = action.action_type === this.navigationItem.action_type;
      const matchesText = text ? new RegExp(text, 'gi').test(action.value) : true;
      return isSameActionType && matchesText;
    });
  }

}
