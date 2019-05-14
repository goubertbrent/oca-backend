import { coerceBooleanProperty } from '@angular/cdk/coercion';
import { CdkDragDrop, moveItemInArray } from '@angular/cdk/drag-drop';
import { ChangeDetectionStrategy, ChangeDetectorRef, Component, EventEmitter, forwardRef, Input, Output } from '@angular/core';
import { ControlContainer, ControlValueAccessor, NG_VALUE_ACCESSOR, NgForm } from '@angular/forms';
import { MatDialog, MatDialogConfig } from '@angular/material/dialog';
import { TranslateService } from '@ngx-translate/core';
import { FormComponentType } from '../../interfaces/enums';
import { FormComponent, FormSection, NextAction, NextActionSection, NextActionType, UINextAction } from '../../interfaces/forms';
import { FormValidatorType } from '../../interfaces/validators';
import { UploadImageDialogComponent } from '../upload-image-dialog/upload-image-dialog.component';

@Component({
  selector: 'oca-edit-form-section',
  templateUrl: './edit-form-section.component.html',
  styleUrls: [ './edit-form-section.component.scss' ],
  changeDetection: ChangeDetectionStrategy.OnPush,
  providers: [ {
    provide: NG_VALUE_ACCESSOR,
    useExisting: forwardRef(() => EditFormSectionComponent),
    multi: true,
  } ],
  viewProviders: [ { provide: ControlContainer, useExisting: NgForm } ],
})
export class EditFormSectionComponent implements ControlValueAccessor {
  set section(value: FormSection) {
    if (this._section) {
      this.onChange(value);
    } else {
      if (value) {
        this.showDescription = !!value.description;
      }
    }
    if (value) {
      this._section = value;
      this._changeDetectorRef.markForCheck();
    }
  }

  get section() {
    return this._section;
  }

  @Input() name: string;
  @Input() readonlyIds = false;
  @Input() formId?: number;
  @Input() headerTitle = '';
  @Input() canMove = false;
  @Input() canDelete = false;
  @Input() showNextAction = false;
  @Input() sectionNumber: number;
  @Input() nextActions: UINextAction[];
  @Input() set canAddComponents(value: any) {
    this._canAddComponents = coerceBooleanProperty(value);
  }
  get canAddComponents() {
    return this._canAddComponents;
  }

  @Output() moveSection = new EventEmitter();
  @Output() deleteSection = new EventEmitter();

  showDescription = false;

  FormComponentType = FormComponentType;
  private _section: FormSection;
  private _canAddComponents = true;
  private onChange = (val: any) => {
  }
  private onTouched = () => {
  }

  constructor(private _translate: TranslateService,
              private _matDialog: MatDialog,
              private _changeDetectorRef: ChangeDetectorRef) {
  }

  changed(property: keyof FormSection, value: any) {
    this.section = { ...this.section, [ property ]: value };
  }

  onRemoveComponent(index: number) {
    const copy = this.section.components;
    copy.splice(index, 1);
    this.section = {
      ...this.section,
      components: copy,
    };
  }

  addComponent() {
    const option = this._translate.instant('oca.option_x', { number: 1 });
    const title = this._translate.instant('oca.untitled_question');
    const choices = [ { label: option, value: option } ];
    this.changed('components', [ ...this.section.components, {
        type: FormComponentType.SINGLE_SELECT,
        description: null,
        choices,
        validators: [ { type: FormValidatorType.REQUIRED } ],
        title,
        id: title,
    } ]);
  }


  registerOnChange(fn: any): void {
    this.onChange = fn;
  }

  registerOnTouched(fn: any): void {
    this.onTouched = fn;
  }

  setDisabledState(isDisabled: boolean): void {
  }

  writeValue(obj: any): void {
    if (obj !== this._section) {
      this.section = obj;
    }
  }

  trackByIndex(index: number) {
    return index;
  }

  componentChanged(component: FormComponent, componentIndex: number) {
    this.section.components  [ componentIndex ] = component;
    this.section = { ...this.section, components: this.section.components };
  }

  dropped(event: CdkDragDrop<FormComponent[ ]>) {
    moveItemInArray(this.section.components, event.previousIndex, event.currentIndex);
  }

  removeHeaderImage() {
    this.section = { ...this.section, branding: null };
  }

  openHeaderImageDialog() {
    const config: MatDialogConfig = {
      data: this.formId,
    };
    this._matDialog.open(UploadImageDialogComponent, config).afterClosed().subscribe((result?: string) => {
      if (result) {
        this.section = { ...this.section, branding: { logo_url: result, avatar_url: null } };
        this._changeDetectorRef.markForCheck();
      }
    });
  }

  compareAction(first: NextAction, second?: NextAction) {
    if (!second) {
      return first.type === NextActionType.NEXT;
    }
    const sameType = first.type === second.type;
    if (sameType && first.type === NextActionType.SECTION) {
      return first.section === (second as NextActionSection).section;
    }
    return sameType;
  }

  trackActions(index: number, action: NextAction) {
    return action.type === NextActionType.SECTION ? `${NextActionType.SECTION}_${action.section}` : action.type;
  }

  toggleDescription() {
    if (this.section.description) {
      this.section = { ...this.section, description: null };
    }
    this.showDescription = !this.showDescription;
  }
}
