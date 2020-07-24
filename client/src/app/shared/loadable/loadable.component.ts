import { ChangeDetectionStrategy, Component, Input, OnChanges, SimpleChanges } from '@angular/core';
import { ErrorService } from '@oca/web-shared';
import { Loadable } from './loadable';

@Component({
  selector: 'oca-loadable',
  templateUrl: './loadable.component.html',
  styleUrls: [ './loadable.component.scss' ],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class LoadableComponent implements OnChanges {
  @Input() loadable: Loadable<any>;
  errorMessage: string;

  constructor(private errorService: ErrorService) {
  }

  ngOnChanges(changes: SimpleChanges): void {
    if (this.loadable.error) {
      this.errorMessage = this.errorService.getErrorMessage(this.loadable.error);
    }
  }
}
