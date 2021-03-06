import { Pipe, PipeTransform } from '@angular/core';
import { MarkedOptions, parse } from 'marked';

@Pipe({
  name: 'markdown',
  pure: true,
})
export class MarkdownPipe implements PipeTransform {

  transform(value: any, options?: MarkedOptions): string {
    return value && parse(value, options);
  }

}
