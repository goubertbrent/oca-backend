import { ChangeDetectionStrategy, Component, EventEmitter, Input, Output, ViewChild } from '@angular/core';
import { NgForm } from '@angular/forms';
import { RunResult, RunScript, Script, ScriptFunction } from '../../scripts';

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
  @ViewChild('form', { static: false }) form: NgForm;

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
    this.run.emit(<RunScript>{ deferred: false, function: func.name, id: (<Script>this.script).id });
  }

  deferFunction(func: ScriptFunction) {
    this.run.emit(<RunScript>{ deferred: true, function: func.name, id: (<Script>this.script).id });
  }

  deleteScript() {
    this.remove.emit(<Script>this.script);
  }

  scrollToFunction(func: ScriptFunction) {
    this._editor.revealLineInCenter(func.line_number, 0); // 0 = ScrollType.Smooth
  }

  trackFunctions(index: number, func: ScriptFunction) {
    return func.name;
  }
}
