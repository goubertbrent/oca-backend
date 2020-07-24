import { NgModule } from '@angular/core';
import { MarkdownPipe } from './markdown.pipe';

export { MarkdownPipe };

@NgModule({
  declarations: [MarkdownPipe],
  exports: [MarkdownPipe],
})
export class MarkdownModule {
}
