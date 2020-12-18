import { ChangeDetectionStrategy, Component, Input } from '@angular/core';
import { IFormGroup } from '@rxweb/types';
import { LinkItemContent, LinkItemSource } from '../homescreen';
import { HomeScreenService } from '../home-screen.service';

@Component({
  selector: 'rcc-link-item-template-content-editor',
  templateUrl: './link-item-template-content-editor.component.html',
  styleUrls: ['./link-item-template-content-editor.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class LinkItemTemplateContentEditorComponent {
  sources = [
    { value: LinkItemSource.NONE, label: 'Custom value' },
    { value: LinkItemSource.SERVICE_INFO_EMAIL, label: 'Service email' },
    { value: LinkItemSource.SERVICE_INFO_PHONE, label: 'Service phone number' },
    { value: LinkItemSource.SERVICE_INFO_WEBSITE, label: 'Service website' },
    { value: LinkItemSource.SERVICE_INFO_ADDRESS, label: 'Service address' },
    { value: LinkItemSource.SERVICE_MENU_ITEM, label: 'Service menu item' },
  ];
  @Input() formGroup: IFormGroup<LinkItemContent>;
  SOURCE_NONE = LinkItemSource.NONE;
  SOURCE_ADDRESS = LinkItemSource.SERVICE_INFO_ADDRESS;
  SOURCE_MENU_ITEM = LinkItemSource.SERVICE_MENU_ITEM;

  constructor(private formService: HomeScreenService) {
  }

  sourceTypeChanged(source: LinkItemSource) {
    let content: LinkItemContent;
    switch (source) {
      case LinkItemSource.NONE:
        content = { source, url: '', external: false, request_user_link: false };
        break;
      case LinkItemSource.SERVICE_INFO_PHONE:
      case LinkItemSource.SERVICE_INFO_EMAIL:
      case LinkItemSource.SERVICE_INFO_WEBSITE:
        content = { source, index: 0 };
        break;
      case LinkItemSource.SERVICE_INFO_ADDRESS:
        content = { source };
        break;
      case LinkItemSource.SERVICE_MENU_ITEM:
        content = { source, service: '', tag: '' };
        break;
      default:
        return;
    }
    const toRemove = new Set(Object.keys(this.formGroup.controls));
    const newForm = this.formService.getLinkItemContentForm(content);
    for (const [name, control] of Object.entries(newForm.controls)) {
      if (toRemove.has(name)) {
        const existingFormGroup = this.formGroup.get(name as any)!;
        existingFormGroup.setValidators(control.validator);
        existingFormGroup.setValue(control.value);
        toRemove.delete(name);
      } else {
        this.formGroup.addControl(name as any, control);
      }
    }
    for (const controlName of toRemove) {
      this.formGroup.removeControl(controlName as any);
    }
  }
}
