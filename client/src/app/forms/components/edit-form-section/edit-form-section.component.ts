import { coerceBooleanProperty } from '@angular/cdk/coercion';
import { CdkDragDrop, moveItemInArray } from '@angular/cdk/drag-drop';
import {
  AfterViewChecked,
  ChangeDetectionStrategy,
  ChangeDetectorRef,
  Component,
  ElementRef,
  EventEmitter,
  forwardRef,
  Input,
  OnDestroy,
  Output,
  QueryList,
  ViewChild,
  ViewChildren,
} from '@angular/core';
import { ControlContainer, ControlValueAccessor, NG_VALUE_ACCESSOR, NgForm } from '@angular/forms';
import { MatDialog, MatDialogConfig } from '@angular/material/dialog';
import { MatToolbar } from '@angular/material/toolbar';
import { TranslateService } from '@ngx-translate/core';
import { MediaType, SimpleDialogComponent, SimpleDialogData, SimpleDialogResult } from '@oca/web-shared';
import { Subscription } from 'rxjs';
import { EASYMDE_OPTIONS } from '../../../../environments/config';
import { UploadedFileResult, UploadFileDialogComponent, UploadFileDialogConfig } from '../../../shared/upload-file';
import { COMPONENT_ICONS } from '../../interfaces/consts';
import { FormComponentType } from '../../interfaces/enums';
import { FormComponent, FormSection, UINextAction } from '../../interfaces/forms';
import { FormValidatorType } from '../../interfaces/validators';
import { generateNewId } from '../../util';

// TODO: convert to reactive forms cuz the template is a bit of a mess
@Component({
  selector: 'oca-edit-form-section',
  templateUrl: './edit-form-section.component.html',
  styleUrls: ['./edit-form-section.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
  providers: [{
    provide: NG_VALUE_ACCESSOR,
    useExisting: forwardRef(() => EditFormSectionComponent),
    multi: true,
  }],
  viewProviders: [{ provide: ControlContainer, useExisting: NgForm }],
})
export class EditFormSectionComponent implements ControlValueAccessor, AfterViewChecked, OnDestroy {
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
  @Input() formId: number;
  @Input() readonlyMode = false;
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

  @ViewChild(MatToolbar, { static: true }) toolbar: MatToolbar;
  @ViewChildren('componentRef') componentRefs: QueryList<HTMLDivElement>;


  @Output() moveSection = new EventEmitter();
  @Output() setActive = new EventEmitter();
  @Output() deleteSection = new EventEmitter();

  showDescription = false;

  /**
   * The index of the component that triggered the 'edit' mode, triggered by clicking a component its title.
   * An attempt will be made to scroll to the component once the 'edit' view is loaded in ngAfterViewChecked.
   */
  editTriggeredByComponent: number | null = null;

  EASYMDE_OPTIONS = EASYMDE_OPTIONS;
  COMPONENT_ICONS = COMPONENT_ICONS;
  FormComponentType = FormComponentType;
  private _section: FormSection;
  private _canAddComponents = true;
  private _componentRefSubscription?: Subscription;
  private onChange = (val: any) => {
  };
  private onTouched = () => {
  };

  constructor(private _translate: TranslateService,
              private _matDialog: MatDialog,
              private _changeDetectorRef: ChangeDetectorRef) {
  }

  ngAfterViewChecked() {
    if (!this._componentRefSubscription) {
      this._componentRefSubscription = this.componentRefs.changes.subscribe((queryList: QueryList<ElementRef<HTMLDivElement>>) => {
        if (this.editTriggeredByComponent !== null && queryList.length > 0) {
          setTimeout(() => {
            if (this.editTriggeredByComponent === -1) {
              this.toolbar._elementRef.nativeElement.scrollIntoView({ behavior: 'smooth', block: 'start' });
            } else {
              const divElement = queryList.find((item, index, array) => index === this.editTriggeredByComponent);
              divElement?.nativeElement?.scrollIntoView({ behavior: 'smooth', block: 'start' });
            }
            this.editTriggeredByComponent = null;
          }, 1);
        }
      });
    }
  }

  ngOnDestroy() {
    this._componentRefSubscription?.unsubscribe();
  }

  changed(property: keyof FormSection, value: any) {
    this.section = { ...this.section, [ property ]: value };
  }

  onRemoveComponent(index: number) {
    const data: SimpleDialogData = {
      message: this._translate.instant('oca.confirm_delete_component'),
      ok: this._translate.instant('oca.Yes'),
      cancel: this._translate.instant('oca.No'),
    };
    this._matDialog.open<SimpleDialogComponent, SimpleDialogData, SimpleDialogResult>(SimpleDialogComponent, { data }).afterClosed()
      .subscribe(result => {
        if (result?.submitted) {
          const copy = this.section.components;
          copy.splice(index, 1);
          this.section = {
            ...this.section,
            components: copy,
          };
          this._changeDetectorRef.markForCheck();
        }
      });
  }

  addComponent() {
    const option = this._translate.instant('oca.option_x', { number: 1 });
    const title = this._translate.instant('oca.untitled_question');
    const choices = [{ label: option, value: option }];
    this.changed('components', [...this.section.components, {
      type: FormComponentType.SINGLE_SELECT,
      description: null,
      choices,
      validators: [{ type: FormValidatorType.REQUIRED }],
      title,
      id: generateNewId(),
    }]);
    this.setActiveByComponent(this.section.components.length - 1);
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
    const config: MatDialogConfig<UploadFileDialogConfig> = {
      data: {
        mediaType: MediaType.IMAGE,
        uploadPrefix: '',
        reference: { type: 'form', id: this.formId },
        title: this._translate.instant('oca.add_header_image'),
        cropOptions: { aspectRatio: 16 / 6 },
      },
    };
    this._matDialog.open(UploadFileDialogComponent, config).afterClosed().subscribe((result?: UploadedFileResult) => {
      if (result) {
        this.section = { ...this.section, branding: { logo_url: result.url, avatar_url: null } };
        this._changeDetectorRef.markForCheck();
      }
    });
  }

  toggleDescription() {
    if (this.section.description) {
      this.section = { ...this.section, description: null };
    }
    this.showDescription = !this.showDescription;
  }

  setActiveByComponent(componentIndex: number) {
    this.editTriggeredByComponent = componentIndex;
    this.setActive.emit();
  }
}
