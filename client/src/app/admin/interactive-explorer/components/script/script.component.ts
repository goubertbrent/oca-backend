import { hasModifierKey } from '@angular/cdk/keycodes';
import {
  ChangeDetectionStrategy,
  Component,
  EventEmitter,
  HostListener,
  Input,
  Output,
  QueryList,
  ViewChild,
  ViewChildren,
} from '@angular/core';
import { NgForm } from '@angular/forms';
import { LastScriptRun, RunResult, RunScript, Script, ScriptFunction } from '../../scripts';

@Component({
  selector: 'oca-ie-script',
  changeDetection: ChangeDetectionStrategy.OnPush,
  templateUrl: 'script.component.html',
  styleUrls: ['script.component.scss'],
})
export class ScriptComponent {
  dateFormat = 'dd/MM/yy HH:mm';
  @Input() loading: boolean;
  @Input() isRunning: boolean;
  @Input() script: Script | null;
  @Input() runResult: RunResult | null;
  @Input() options: any = {};
  @Output() save = new EventEmitter<Script>();
  @Output() run = new EventEmitter<RunScript>();
  @Output() remove = new EventEmitter<Script>();
  @Output() showFullscreen = new EventEmitter<RunResult>();
  @ViewChild('form') form: NgForm;
  @ViewChildren('runButton') runButtons: QueryList<HTMLAnchorElement>;

  @HostListener('window:keydown', ['$event'])
  onKeyUp(event: KeyboardEvent) {
    if (hasModifierKey(event, 'ctrlKey') || event.metaKey) {
      if (event.key === 's') {
        event.preventDefault();
        this.submit();
      } else if (event.key === 'r') {
        event.preventDefault();
        // re-run last ran script
        if (this.script && this.script.functions.length) {
          const funcs = this.script.functions
            .filter(f => f.last_run !== null)
            .sort((f1, f2) => {
              return new Date((f2.last_run as LastScriptRun).date).getTime() - new Date((f1.last_run as LastScriptRun).date).getTime();
            });
          if (funcs.length) {
            this.runFunction(funcs[ 0 ]);
          }
        }
      } else if (['1', '2', '3', '4', '5', '6', '7', '8', '9', '0'].includes(event.key)) {
        event.preventDefault();
        const number = parseInt(event.key, 10);
        const buttons = this.runButtons.toArray();
        const index = number === 0 ? 10 : number - 1;
        if (index in buttons) {
          buttons[ number - 1 ].focus();
        }
      }
    } else if (event.key === 'F11' && this.runResult) {
      event.preventDefault();
      this.showFullscreen.emit(this.runResult);
    }
  }

  /**
   * Reference to the monaco editor
   */
  private _editor: any;

  onMonacoInit(editor: any) {
    this._editor = editor;
  }

  submit() {
    if (this.form.form.valid) {
      this.save.emit(this.script as Script);
    }
  }

  runFunction(func: ScriptFunction) {
    this.run.emit({ deferred: false, function: func.name, id: (this.script as Script).id });
  }

  deferFunction(func: ScriptFunction) {
    this.run.emit({ deferred: true, function: func.name, id: (this.script as Script).id });
  }

  deleteScript() {
    this.remove.emit(this.script as Script);
  }

  scrollToFunction(func: ScriptFunction) {
    this._editor.revealLineInCenter(func.line_number, 0); // 0 = ScrollType.Smooth
  }

  trackFunctions(index: number, func: ScriptFunction) {
    return func.name;
  }
}
