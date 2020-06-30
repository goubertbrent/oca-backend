import { Pipe, PipeTransform } from '@angular/core';
import { DynamicDatePipe } from '@oca/shared';
import { HoplrFeedItem, HoplrMessageType } from '../hoplr';

@Pipe({
  name: 'itemSubHeader',
  pure: false,
})
export class ItemSubHeaderPipe implements PipeTransform {

  constructor(private dynamicDatePipe: DynamicDatePipe) {
  }

  transform(value: HoplrFeedItem): string | null {
    const date = this.dynamicDatePipe.transform(value.data.CreatedAt, true);
    switch (value.type) {
      case HoplrMessageType.MESSAGE:
        const parts = [date, value.data.User.ProfileName];
        if(value.data.User.Profile?.FunctionTitle) {
          parts.push(value.data.User.Profile?.FunctionTitle);
        }
        return parts.join(' - ');
      default:
        return date;
    }
  }

}
