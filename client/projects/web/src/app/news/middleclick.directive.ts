import { Directive, EventEmitter, HostListener, Output } from '@angular/core';

@Directive({ selector: '[middleclick]' })
export class MiddleclickDirective {
  @Output() middleclick = new EventEmitter();

  @HostListener('mouseup', ['$event'])
  middleclickEvent(event: MouseEvent) {
    if (event.which === 2) {
      this.middleclick.emit(event);
    }
  }
}
