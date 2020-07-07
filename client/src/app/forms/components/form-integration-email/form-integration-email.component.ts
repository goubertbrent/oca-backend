import { ChangeDetectionStrategy, Component, EventEmitter, Input, OnChanges, Output, SimpleChanges } from '@angular/core';
import { FormControl, FormGroup, Validators } from '@angular/forms';
import { MatDialog, MatDialogConfig } from '@angular/material/dialog';
import { TranslateService } from '@ngx-translate/core';
import { SimpleDialogComponent, SimpleDialogData } from '../../../shared/dialog/simple-dialog.component';
import { updateItem } from '../../../shared/util';
import { FormComponentType } from '../../interfaces/enums';
import { FormSection, SingleSelectComponent, Value } from '../../interfaces/forms';
import { EmailComponentMapping, EmailGroup, EmailIntegrationFormConfig } from '../../interfaces/integrations';

interface SectionsMapping {
  [ key: string ]: {
    section: FormSection; components: {
      [ key: string ]: {
        component: SingleSelectComponent;
        choices: {
          [ key: string ]: Value
        };
      };
    };
  };
}

interface UIMapping {
  page: string;
  component: string;
  value: string;
  recipients: string;
  mapping: EmailComponentMapping;
}

@Component({
  selector: 'oca-form-integration-email',
  templateUrl: './form-integration-email.component.html',
  styleUrls: ['./form-integration-email.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class FormIntegrationEmailComponent implements OnChanges {
  @Input() configuration: EmailIntegrationFormConfig;
  @Output() configurationChanged = new EventEmitter<EmailIntegrationFormConfig>();
  newEmailControl = new FormControl(null, [Validators.required, Validators.email]);
  groupForm = new FormGroup({
    id: new FormControl(0),
    name: new FormControl(null),
    emails: new FormControl([], [Validators.required]),
    newEmail: this.newEmailControl,
  });
  mappingForm = new FormGroup({
    section: new FormControl(null),
    component: new FormControl(null),
    value: new FormControl(null),
    group: new FormControl(null),
  });
  NEW_ITEM_INDEX = -1;
  editingGroupIndex: number | null = null;
  editingMappingIndex: number | null = null;
  sectionsMapping: SectionsMapping = {};
  displayMapping: UIMapping[] = [];

  private _sections: FormSection[];

  get sections() {
    return this._sections;
  }

  @Input() set sections(value: FormSection[]) {
    this._sections = value;
    this.sectionsMapping = {};
    for (const section of this.sections) {
      const components: any = {};
      this.sectionsMapping[ section.id ] = { section, components };
      for (const component of section.components) {
        if (component.type === FormComponentType.SINGLE_SELECT) {
          const choices: { [ key: string ]: Value } = {};
          for (const choice of component.choices) {
            choices[ choice.value ] = choice;
          }
          components[ component.id ] = { component, choices };
        }
      }
    }
  }

  constructor(private matDialog: MatDialog,
              private translate: TranslateService) {
  }

  ngOnChanges(changes: SimpleChanges) {
    if (changes.sections || changes.configuration) {
      this.setDisplayMapping();
    }
  }

  saveMapping() {
    if (!this.mappingForm.valid) {
      return;
    }
    const { section, component, value, group } = this.mappingForm.value as {
      section: FormSection,
      component: SingleSelectComponent,
      value: Value;
      group: EmailGroup
    };
    this.configuration.mapping.push({
      section_id: section.id,
      component_id: component.id,
      component_value: value.value,
      group_id: group.id,
    });
    this.setConfig({ mapping: this.configuration.mapping });
    this.editingMappingIndex = null;
  }

  removeMapping(mapping: EmailComponentMapping) {
    this.setConfig({ mapping: this.configuration.mapping.filter(m => m !== mapping) });
  }

  trackSections(index: number, section: FormSection) {
    return section.id;
  }

  trackComponentChoices(index: number, component: SingleSelectComponent) {
    return component.id;
  }

  removeEmail(email: string) {
    const control = this.groupForm.controls.emails;
    control.setValue(control.value.filter((e: string) => e !== email));
  }

  addEmail() {
    this.groupForm.markAllAsTouched();
    if (!this.newEmailControl.valid) {
      return;
    }
    const trimmed = this.newEmailControl.value.trim();
    const control = this.groupForm.controls.emails;
    const emails = control.value;
    if (!emails.includes(trimmed)) {
      emails.push(trimmed);
      control.setValue(emails);
    }
    this.newEmailControl.reset();
  }

  saveGroup() {
    this.addEmail();
    this.newEmailControl.reset();
    const { id, name, emails }: EmailGroup = this.groupForm.value;
    const newGroup = { id, name, emails };
    const existingGroup = this.configuration.email_groups.find(g => g.id === id);
    let groups = this.configuration.email_groups;
    if (existingGroup) {
      groups = updateItem(groups, newGroup, 'id');
    } else {
      groups.push(newGroup);
    }
    this.setConfig({
      email_groups: groups,
      default_group: this.configuration.default_group ?? newGroup.id,
    });
    this.editingGroupIndex = null;
  }

  deleteGroup(group: EmailGroup) {
    const foundItems = this.configuration.mapping.filter(m => m.group_id === group.id);
    if (foundItems.length > 0) {
      const questions:[EmailComponentMapping, SingleSelectComponent][] = foundItems
        .map(item => [item, this.sectionsMapping[ item.section_id ]?.components[ item.component_id ]?.component]);
      const questionsList:string[] = questions.map(([g, component]) => component?.title ?? g.component_value);
      const config: MatDialogConfig<SimpleDialogData> = {
        data: {
          ok: this.translate.instant('oca.ok'),
          title: this.translate.instant('oca.Error'),
          message: this.translate.instant('oca.email_group_still_in_use', { questions: questionsList.join(',') }),
        }
      };
      this.matDialog.open(SimpleDialogComponent, config);
      return;
    }
    const newGroups = this.configuration.email_groups.filter(g => g.id !== group.id);
    let defaultGroupId = this.configuration.default_group;
    if (defaultGroupId === group.id) {
      if (newGroups.length > 0) {
        defaultGroupId = newGroups[ 0 ].id;
      } else {
        defaultGroupId = null;
      }
    }
    this.setConfig({ email_groups: newGroups, default_group: defaultGroupId });
  }

  editGroup(group: EmailGroup) {
    this.editingGroupIndex = this.configuration.email_groups.indexOf(group);
    this.groupForm.patchValue(group);
  }

  addGroup() {
    this.editingGroupIndex = this.NEW_ITEM_INDEX;
    this.groupForm.reset();
    this.groupForm.patchValue({ id: this.findNextGroupId(), emails: [] });
  }

  setDefaultGroup($event: number) {
    this.setConfig({ default_group: $event });
  }

  addMapping() {
    this.editingMappingIndex = this.NEW_ITEM_INDEX;
    this.mappingForm.reset();
  }

  setConfig(update: Partial<EmailIntegrationFormConfig>) {
    this.configuration = { ...this.configuration, ...update };
    this.configurationChanged.emit(this.configuration);
    this.setDisplayMapping();
  }

  private setDisplayMapping() {
    this.displayMapping = [];
    const recipientsMapping = new Map(this.configuration.email_groups.map(group => [group.id, group]));
    for (const mapping of this.configuration.mapping) {
      const sectionMapping = this.sectionsMapping[ mapping.section_id ];
      const componentMapping = sectionMapping?.components[ mapping.component_id ];
      const choiceMapping = componentMapping?.choices[ mapping.component_value ];
      const recipients = recipientsMapping.get(mapping.group_id);
      let recipientsLabel = '';
      if (recipients) {
        if (recipients.name) {
          recipientsLabel = recipients.name + ' - ';
        }
        recipientsLabel += recipients.emails.join(', ');
      }
      this.displayMapping.push({
        page: sectionMapping?.section?.title ?? '',
        component: componentMapping?.component?.title ?? '',
        value: choiceMapping?.label ?? '',
        recipients: recipientsLabel,
        mapping,
      });
    }
  }

  private findNextGroupId() {
    let largestId = 0;
    for (const group of this.configuration.email_groups) {
      if (group.id > largestId) {
        largestId = group.id;
      }
    }
    return largestId + 1;
  }
}
