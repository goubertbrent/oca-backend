import { coerceBooleanProperty } from '@angular/cdk/coercion';
import { CdkDragDrop, moveItemInArray } from '@angular/cdk/drag-drop';
import { ChangeDetectionStrategy, Component, forwardRef, Input } from '@angular/core';
import { ControlContainer, ControlValueAccessor, NG_VALUE_ACCESSOR, NgForm } from '@angular/forms';
import { TranslateService } from '@ngx-translate/core';
import { FormComponentType } from '../../../interfaces/enums';
import { FormComponent, FormSection } from '../../../interfaces/forms.interfaces';

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
    this._section = value;
    this.onChange(value);
  }

  get section() {
    return this._section;
  }

  @Input() name: string;
  @Input() set canAddComponents(value: any) {
    this._canAddComponents = coerceBooleanProperty(value);
  }
  get canAddComponents() {
    return this._canAddComponents;
  }

  FormComponentType = FormComponentType;
  private _section: FormSection;
  private _canAddComponents = true;
  private onChange = (val: any) => {
  };
  private onTouched = () => {
  };

  constructor(private _translate: TranslateService) {
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
    this.section = {
      ...this.section,
      components: [ ...this.section.components, {
        type: FormComponentType.SINGLE_SELECT,
        description: null,
        choices,
        validators: [],
        title,
        id: title,
      } ],
    };
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
}
