import { Injectable, Pipe, PipeTransform } from '@angular/core';
import * as marked from 'marked';

@Injectable()
@Pipe({ name: 'markdown', pure: true })
export class MarkdownPipe implements PipeTransform {
  static setOptions(options: marked.MarkedOptions): void {
    marked.setOptions(options);
  }

  transform(value: string | null, options?: marked.MarkedOptions) {
    return value ? marked(value, options) : '';
  }
}
