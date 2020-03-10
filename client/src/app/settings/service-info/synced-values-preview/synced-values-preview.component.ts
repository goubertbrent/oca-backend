import { ChangeDetectionStrategy, Component, Input, ViewEncapsulation } from '@angular/core';
import { SyncedNameValue } from '../service-info';

@Component({
  selector: 'oca-synced-values-preview',
  templateUrl: './synced-values-preview.component.html',
  changeDetection: ChangeDetectionStrategy.OnPush,
  encapsulation: ViewEncapsulation.None,
})
export class SyncedValuesPreviewComponent {
  @Input() values: SyncedNameValue[];
}
