import { ChangeDetectionStrategy, ChangeDetectorRef, Component, EventEmitter, Input, OnInit, Output } from '@angular/core';
import { FormBuilder, Validators } from '@angular/forms';
import { MatDialog } from '@angular/material/dialog';
import { TranslateService } from '@ngx-translate/core';
import { SimpleDialogComponent, SimpleDialogData } from '@oca/web-shared';
import { IFormBuilder, IFormGroup } from '@rxweb/types';
import { Observable } from 'rxjs';
import { shareReplay, startWith } from 'rxjs/operators';
import { insertItem, removeItem, updateItem } from '../../../shared/util';
import { FormsService } from '../../forms.service';
import { COMPONENT_ICONS } from '../../interfaces/consts';
import { FormComponentType } from '../../interfaces/enums';
import { FormSection, InputComponents, isInputComponent } from '../../interfaces/forms';
import { FormValidatorType } from '../../interfaces/validators';
import {
  OptionalFieldLocationFormat,
  OptionalFieldsOptions,
  TOPDeskBriefDescriptionMapping,
  TOPDeskCategory,
  TOPDeskCategoryMapping,
  TOPDeskComponentMapping,
  TOPDeskIntegrationFormConfig,
  TOPDeskOptionalField1Mapping,
  TOPDeskOptionalField2Mapping,
  TOPDeskPropertyName,
  TOPDeskSectionMapping,
  TOPDeskSubCategory,
  TOPDeskSubCategoryMapping,
  TOPDeskSupportedMappingTypes,
} from '../integrations';

const ALLOWED_COMPONENT_TYPES_FOR_MAPPING_TYPE = {
  [ TOPDeskPropertyName.CATEGORY ]: [FormComponentType.SINGLE_SELECT],
  [ TOPDeskPropertyName.SUBCATEGORY ]: [FormComponentType.SINGLE_SELECT],
  [ TOPDeskPropertyName.BRIEF_DESCRIPTION ]: [FormComponentType.SINGLE_SELECT, FormComponentType.TEXT_INPUT],
  [ TOPDeskPropertyName.OPTIONAL_FIELDS_1 ]: [FormComponentType.LOCATION],
  [ TOPDeskPropertyName.OPTIONAL_FIELDS_2 ]: [FormComponentType.LOCATION],
};

@Component({
  selector: 'oca-form-integration-topdesk',
  templateUrl: './form-integration-topdesk.component.html',
  styleUrls: ['./form-integration-topdesk.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class FormIntegrationTOPDeskComponent implements OnInit {
  @Output() configurationChanged = new EventEmitter<TOPDeskIntegrationFormConfig>();
  editingFormGroup: IFormGroup<TOPDeskComponentMapping>;
  editing: { index: number, section: string } | null = null;
  possibleComponents: InputComponents[] = [];
  selectedComponent: InputComponents | null = null;
  categories$: Observable<TOPDeskCategory[]>;
  subCategories$: Observable<TOPDeskSubCategory[]>;
  NEW_ITEM_INDEX = -1;
  TOPDeskPropertyName = TOPDeskPropertyName;
  /**
   * Mapping of section id to the list of mappings of topdesk component to form component
   */
  sectionsMapping = new Map<string, TOPDeskComponentMapping[]>();
  /**
   * Contains all input components, indexed by section id and component id.
   */
  componentsMapping = new Map<string, Map<string, InputComponents>>();
  /**
   * Contains all components that have no mapping on topdesk assigned to them.
   * These components and their value will be added to the 'request' field when creating an incident.
   */
  unassignedComponents = new Map<string, InputComponents[]>();

  COMPONENT_ICONS = COMPONENT_ICONS;
  MAPPING_LABELS: { [key in TOPDeskSupportedMappingTypes]: string } = {
    [ TOPDeskPropertyName.CATEGORY ]: 'oca.category',
    [ TOPDeskPropertyName.SUBCATEGORY ]: 'oca.subcategory',
    [ TOPDeskPropertyName.BRIEF_DESCRIPTION ]: 'oca.brief_description',
    [ TOPDeskPropertyName.OPTIONAL_FIELDS_1 ]: 'oca.optional_fields_1',
    [ TOPDeskPropertyName.OPTIONAL_FIELDS_2 ]: 'oca.optional_fields_2',
  };
  MAPPING_TYPES: { type: TOPDeskSupportedMappingTypes, label: string }[] = Object.entries(this.MAPPING_LABELS)
    .map(([type, label]: [TOPDeskSupportedMappingTypes, string]) => ({ type, label }));

  private formBuilder: IFormBuilder;

  constructor(formBuilder: FormBuilder,
              private changeDetectorRef: ChangeDetectorRef,
              private translate: TranslateService,
              private formsService: FormsService,
              private matDialog: MatDialog) {
    this.formBuilder = formBuilder;
    this.categories$ = this.formsService.getTOPDeskCategories().pipe(shareReplay());
    this.subCategories$ = this.formsService.getTOPDeskSubCategories().pipe(shareReplay());
  }

  private _sections: FormSection[];

  get sections() {
    return this._sections;
  }

  @Input() set sections(value: FormSection[]) {
    this._sections = value;
    this.componentsMapping.clear();
    for (const section of value) {
      const inputComponents = section.components.filter(c => isInputComponent(c)) as InputComponents[];
      this.componentsMapping.set(section.id, new Map(inputComponents.map(c => [c.id, c])));
      this.setUnassignedComponents(section.id);
    }
  }

  private _configuration: TOPDeskIntegrationFormConfig;

  get configuration() {
    return this._configuration;
  }

  @Input() set configuration(value: TOPDeskIntegrationFormConfig) {
    this._configuration = value;
    this.sectionsMapping.clear();
    for (const mapping of value.mapping) {
      this.sectionsMapping.set(mapping.id, mapping.components);
      this.setUnassignedComponents(mapping.id);
    }
  }

  ngOnInit(): void {
  }

  trackSections(index: number, section: FormSection) {
    return section.id;
  }

  addMapping(section: FormSection, mappingType: TOPDeskSupportedMappingTypes) {
    const allowedTypes = ALLOWED_COMPONENT_TYPES_FOR_MAPPING_TYPE[ mappingType ];
    const component = section.components.find(c => allowedTypes.includes(c.type)) as InputComponents | undefined;
    if (component) {
      this.setEditing(section, this.NEW_ITEM_INDEX, this.getNewMapping(mappingType, component.id));
    } else {
      const data: SimpleDialogData = {
        title: this.translate.instant('oca.Error'),
        message: this.translate.instant('oca.no_available_components_for_this_type'),
        ok: this.translate.instant('oca.ok'),
      };
      this.matDialog.open<SimpleDialogComponent, SimpleDialogData>(SimpleDialogComponent, { data });
    }
  }

  editMapping(componentIndex: number, section: FormSection, mapping: TOPDeskComponentMapping) {
    this.setEditing(section, componentIndex, mapping);
  }

  removeMapping(index: number, section: FormSection, component: TOPDeskComponentMapping) {
    const currentSection = this.configuration.mapping.find(m => m.id === section.id)!;
    let updatedMapping: TOPDeskSectionMapping[];
    if (currentSection.components.length === 1) {
      this.sectionsMapping.delete(section.id);
      updatedMapping = removeItem(this.configuration.mapping, currentSection, 'id');
    } else {
      const components = removeItem(currentSection.components, component, 'id');
      updatedMapping = updateItem(this.configuration.mapping, { ...currentSection, components }, 'id');
      this.sectionsMapping.set(section.id, components);
    }
    this._configuration = { ...this.configuration, mapping: updatedMapping };
    this.setUnassignedComponents(section.id);
    this.configurationChanged.emit(this._configuration);
  }

  updateMapping() {
    if (this.editingFormGroup.invalid) {
      return;
    }
    const section = this.editing!.section;
    let mapping: TOPDeskSectionMapping[];
    const conf = this.configuration.mapping.find(c => c.id === section);
    // update this section its mapping
    const updatedComponent = this.editingFormGroup.value!;
    let updatedComponents: TOPDeskComponentMapping[];
    if (conf) {
      if (this.editing!.index === this.NEW_ITEM_INDEX) {
        updatedComponents = [...conf.components, updatedComponent];
        mapping = updateItem(this.configuration.mapping, { ...conf, components: updatedComponents }, 'id');
      } else {
        updatedComponents = [...conf.components];  // take copy as to not modify the original array
        updatedComponents[ this.editing!.index ] = updatedComponent;
        mapping = updateItem(this.configuration.mapping, { id: section, components: updatedComponents }, 'id');
      }
    } else {
      // section not yet in config, create it.
      updatedComponents = [updatedComponent];
      mapping = insertItem(this.configuration.mapping, { id: section, components: updatedComponents });
    }
    this.sectionsMapping.set(section, updatedComponents);
    this.editing = null;
    this._configuration = { ...this.configuration, mapping };
    this.setUnassignedComponents(section);
    this.configurationChanged.emit(this._configuration);
  }

  private setEditing(section: FormSection, componentIndex: number, mapping: TOPDeskComponentMapping) {
    this.editing = {
      index: componentIndex,
      section: section.id,
    };
    this.editingFormGroup = this.getFormForComponent(mapping);
    const allowedTypes = ALLOWED_COMPONENT_TYPES_FOR_MAPPING_TYPE[ mapping.type ];
    this.possibleComponents = section.components.filter(component => allowedTypes.includes(component.type)) as InputComponents[];
    this.editingFormGroup.controls.id.valueChanges.pipe(startWith(mapping.id)).subscribe(idValue => {
      this.selectedComponent = this.possibleComponents.find(c => c.id === idValue)!;
    });
  }

  private getFormForComponent(component: TOPDeskComponentMapping): IFormGroup<TOPDeskComponentMapping> {
    switch (component.type) {
      case TOPDeskPropertyName.CATEGORY:
        return this.formBuilder.group<TOPDeskCategoryMapping>({
          type: this.formBuilder.control(component.type),
          id: this.formBuilder.control(component.id, Validators.required),
          categories: this.formBuilder.control(component.categories),
        });
      case TOPDeskPropertyName.SUBCATEGORY:
        return this.formBuilder.group<TOPDeskSubCategoryMapping>({
          type: this.formBuilder.control(component.type),
          id: this.formBuilder.control(component.id, Validators.required),
          subcategories: this.formBuilder.control(component.subcategories),
        });
      case TOPDeskPropertyName.BRIEF_DESCRIPTION:
        return this.formBuilder.group<TOPDeskBriefDescriptionMapping>({
          type: this.formBuilder.control(component.type),
          id: this.formBuilder.control(component.id, Validators.required),
        });
      case TOPDeskPropertyName.OPTIONAL_FIELDS_1:
        return this.formBuilder.group<TOPDeskOptionalField1Mapping>({
          type: this.formBuilder.control(component.type),
          id: this.formBuilder.control(component.id, Validators.required),
          field: this.formBuilder.control(component.field),
          options: this.getOptionalFieldOptionsForm(component.options),
        });
      case TOPDeskPropertyName.OPTIONAL_FIELDS_2:
        return this.formBuilder.group<TOPDeskOptionalField2Mapping>({
          type: this.formBuilder.control(component.type),
          id: this.formBuilder.control(component.id, Validators.required),
          field: this.formBuilder.control(component.field),
          options: this.getOptionalFieldOptionsForm(component.options),
        });
    }
  }

  private setUnassignedComponents(sectionId: string) {
    const sectionMappings = this.sectionsMapping.get(sectionId);
    const componentsMapping = this.componentsMapping.get(sectionId);
    if (!componentsMapping) {
      return;
    }
    const components = Array.from(componentsMapping.values());
    if (sectionMappings) {
      const usedComponentIds = sectionMappings.map(comp => comp.id);
      const unassigned = components.filter(c => !usedComponentIds.includes(c.id));
      this.unassignedComponents.set(sectionId, unassigned);
    } else {
      this.unassignedComponents.set(sectionId, components);
    }
  }

  private getOptionalFieldOptionsForm(options: OptionalFieldsOptions) {
    return this.formBuilder.group<OptionalFieldsOptions>(
      {
        type: this.formBuilder.control(options.type),
        format: this.formBuilder.control(options.format),
      },
    );
  }

  private getNewMapping(type: TOPDeskSupportedMappingTypes, id: string): TOPDeskComponentMapping {
    switch (type) {
      case TOPDeskPropertyName.BRIEF_DESCRIPTION:
        return { type, id };
      case TOPDeskPropertyName.CATEGORY:
        return { type, id, categories: {} };
      case TOPDeskPropertyName.SUBCATEGORY:
        return { type, id, subcategories: {} };
      case TOPDeskPropertyName.OPTIONAL_FIELDS_1:
      case TOPDeskPropertyName.OPTIONAL_FIELDS_2:
        return {
          type,
          id,
          field: 'text1',
          options: { type: FormComponentType.LOCATION, format: OptionalFieldLocationFormat.LATITUDE_LONGITUDE },
        };
    }
    throw new Error(`type ${type} not implemented`);
  }
}
