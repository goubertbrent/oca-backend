import { ChangeDetectionStrategy, Component, Input } from '@angular/core';
import { IFormGroup } from '@rxweb/types';
import { OptionalFieldLocationFormat, TOPDeskOptionalFields, TOPDeskOptionalFieldsMapping } from '../integrations';

@Component({
  selector: 'oca-topdesk-optional-field-mapping',
  templateUrl: './topdesk-optional-field-mapping.component.html',
  styleUrls: ['./topdesk-optional-field-mapping.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class TOPDeskOptionalFieldMappingComponent {
  @Input() formGroup: IFormGroup<TOPDeskOptionalFieldsMapping>;
  LOCATION_FORMATS = [
    { type: OptionalFieldLocationFormat.LATITUDE_LONGITUDE, label: 'oca.latitude_and_longitude_in_one_field' },
    { type: OptionalFieldLocationFormat.LATITUDE, label: 'oca.latitude' },
    { type: OptionalFieldLocationFormat.LONGITUDE, label: 'oca.longitude' },
  ];

  TOPDESK_FIELDS = Object.values(TOPDeskOptionalFields);
}
