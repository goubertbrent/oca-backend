import { CdkDragDrop, moveItemInArray } from '@angular/cdk/drag-drop';
import { ChangeDetectionStrategy, Component, EventEmitter, Input, OnDestroy, Output } from '@angular/core';
import { FormBuilder, Validators } from '@angular/forms';
import { IFormArray, IFormBuilder, IFormGroup } from '@rxweb/types';
import { Observable, Subject } from 'rxjs';
import { auditTime, map } from 'rxjs/operators';
import { FA_ICONS, filterIcons, FontAwesomeIcon, iconValidator } from '../../../constants';
import { TranslationInternal, TranslationValue } from '../homescreen';
import { HomeScreenBottomNavigation, HomeScreenNavigationButton } from '../models';

@Component({
  selector: 'rcc-home-screen-bottom-navigation',
  templateUrl: './home-screen-bottom-navigation.component.html',
  styleUrls: ['./home-screen-bottom-navigation.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class HomeScreenBottomNavigationComponent implements OnDestroy {
  faIcons = FA_ICONS;

  filteredIcons$: Observable<FontAwesomeIcon[]>;

  @Input() formGroup: IFormGroup<HomeScreenBottomNavigation>;
  @Input() translations: TranslationInternal[];
  @Input() translationsMapping: TranslationValue = {};
  @Output() addTranslationClicked = new EventEmitter();

  editingBottomNavFormGroup: IFormGroup<HomeScreenNavigationButton>;
  editingBottomNavIndex = -1;

  private formBuilder: IFormBuilder;
  private destroyed$ = new Subject();

  constructor(formBuilder: FormBuilder) {
    this.formBuilder = formBuilder;
    this.editingBottomNavFormGroup = this.getNavigationButtonFormGroup({ icon: 'fa-home', label: '$home', action: '' });
    this.filteredIcons$ = this.editingBottomNavFormGroup.controls.icon.valueChanges.pipe(
      auditTime(300),
      map(text => Array.from(filterIcons(text ?? ''))),
    );
  }

  get canAddBottomNavButton() {
    return this.editingBottomNavIndex === -1 && this.bottomNavButtonsForm.value.length < 5;
  }

  get bottomNavButtonsForm(): IFormArray<HomeScreenNavigationButton> {
    return this.formGroup.controls.buttons as IFormArray<HomeScreenNavigationButton>;
  }

  ngOnDestroy() {
    this.destroyed$.next();
    this.destroyed$.complete();
  }

  setEditing(btn: HomeScreenNavigationButton, index: number) {
    this.editingBottomNavIndex = index;
    this.editingBottomNavFormGroup.setValue(btn, { emitEvent: false });
  }

  saveBottomNavButton() {
    if (this.editingBottomNavFormGroup.valid) {
      this.bottomNavButtonsForm.at(this.editingBottomNavIndex).setValue(this.editingBottomNavFormGroup.value);
      this.editingBottomNavIndex = -1;
    }
  }

  removeBottomNavButton(index: number) {
    this.bottomNavButtonsForm.removeAt(index);
  }

  addBottomNavButton() {
    const btn = { icon: 'fa-home', label: '', action: '' };
    this.bottomNavButtonsForm.push(this.getNavigationButtonFormGroup(btn));
    const index = this.bottomNavButtonsForm.value.length - 1;
    this.setEditing(btn, index);
  }

  moveBottomNavigationButton(event: CdkDragDrop<HomeScreenNavigationButton[]>) {
    const array = this.bottomNavButtonsForm.value;
    moveItemInArray(array, event.previousIndex, event.currentIndex);
    this.bottomNavButtonsForm.setValue(array);
  }

  private getNavigationButtonFormGroup(navButton: HomeScreenNavigationButton) {
    return this.formBuilder.group<HomeScreenNavigationButton>({
      label: this.formBuilder.control(navButton.label, Validators.required),
      action: this.formBuilder.control(navButton.action, Validators.required),
      icon: this.formBuilder.control(navButton.icon, [Validators.required, iconValidator]),
    });
  }
}
