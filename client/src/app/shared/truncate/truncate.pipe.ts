import { Pipe, PipeTransform } from '@angular/core';

@Pipe({
  name: 'truncate',
  pure: true,
})
export class TruncatePipe implements PipeTransform {

  transform(value: string | null, limit: number, trail: string = '…'): string {
    if (!value) {
      return '';
    }
    return value.length > limit ? value.substring(0, limit) + trail : value;
  }

}
