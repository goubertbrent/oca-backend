import { DatePipe } from '@angular/common';
import { ChangeDetectionStrategy, Component, EventEmitter, Input, Output } from '@angular/core';
import { MatDialog, MatDialogConfig } from '@angular/material/dialog';
import { MatSlideToggleChange } from '@angular/material/slide-toggle';
import { TranslateService } from '@ngx-translate/core';
import { SimpleDialogComponent, SimpleDialogData, SimpleDialogResult } from '../../../shared/dialog/simple-dialog.component';
import { OpeningHourException, OpeningHours, OpeningHourType, OpeningPeriod } from '../../../shared/interfaces/oca';
import { HoursPipe } from '../../pipes/hours.pipe';

@Component({
  selector: 'oca-opening-hours',
  templateUrl: './opening-hours.component.html',
  styleUrls: ['./opening-hours.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class OpeningHoursComponent {
  @Input() openingHours: OpeningHours;
  @Input() isLoading: boolean;
  @Output() saved = new EventEmitter<OpeningHours>();
  @Output() hoursChanged = new EventEmitter<OpeningHours>();

  constructor(private hoursPipe: HoursPipe,
              private datePipe: DatePipe,
              private translate: TranslateService,
              private matDialog: MatDialog) {
  }

  updateDate(exception: OpeningHourException, property: 'start_date' | 'end_date', value: Date | null, index: number) {
    if (value) {
      exception[ property ] = this.datePipe.transform(value, 'yyyy-MM-dd') as string;
      this.updateExceptionPeriodsAtIndex(exception, index);
    }
  }

  updateExceptionPeriods(exception: OpeningHourException, $event: OpeningPeriod[], index: number) {
    this.updateExceptionPeriodsAtIndex({ ...exception, periods: $event }, index);
  }

  updateExceptionPeriodsAtIndex(exception: OpeningHourException, index: number) {
    const exceptions = this.openingHours.exceptional_opening_hours;
    exceptions[ index ] = exception;
    this.setChanged({ ...this.openingHours, exceptional_opening_hours: exceptions });
  }

  addException() {
    const today = new Date().toISOString().split('T')[ 0 ];
    const exception: OpeningHourException = { start_date: today, end_date: today, periods: [], description: null };
    this.setChanged({ ...this.openingHours, exceptional_opening_hours: [...this.openingHours.exceptional_opening_hours, exception] });
  }

  removeException(exception: OpeningHourException) {
    this.setChanged({
      ...this.openingHours,
      exceptional_opening_hours: this.openingHours.exceptional_opening_hours.filter(e => e !== exception),
    });
  }

  trackByIndex(index: number, element: any) {
    return index;
  }

  updatePeriods(periods: OpeningPeriod[]) {
    this.setChanged({ ...this.openingHours, periods, type: OpeningHourType.STRUCTURED });
  }

  private setChanged(openingHours: OpeningHours) {
    this.openingHours = openingHours;
    this.hoursChanged.next(this.openingHours);
  }

  toggleNotRelevant($event: MatSlideToggleChange) {
    if ([OpeningHourType.STRUCTURED, OpeningHourType.TEXTUAL].includes(this.openingHours.type)) {
      if (this.openingHours.periods.length > 0 || this.openingHours.exceptional_opening_hours.length > 0) {
        const config: MatDialogConfig<SimpleDialogData> = {
          data: {
            ok: this.translate.instant('oca.Yes'),
            cancel: this.translate.instant('oca.No'),
            message: this.translate.instant('oca.this_will_remove_your_existing_hours'),
          },
        };
        this.matDialog.open(SimpleDialogComponent, config).afterClosed().subscribe((result?: SimpleDialogResult) => {
          if (result?.submitted) {
            this.setChanged({ ...this.openingHours, type: OpeningHourType.NOT_RELEVANT, periods: [], exceptional_opening_hours: [] });
          } else {
            $event.source.checked = false;
          }
        });
      } else {
        this.setChanged({ ...this.openingHours, type: OpeningHourType.NOT_RELEVANT, periods: [], exceptional_opening_hours: [] });
      }
    } else {
      this.setChanged({ ...this.openingHours, type: OpeningHourType.STRUCTURED });
    }
  }
}
