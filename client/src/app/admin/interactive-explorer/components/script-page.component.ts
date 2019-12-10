import { ChangeDetectionStrategy, Component, OnInit, ViewEncapsulation } from '@angular/core';
import { MatDialog } from '@angular/material/dialog';
import { ActivatedRoute, Router } from '@angular/router';
import { select, Store } from '@ngrx/store';
import { TranslateService } from '@ngx-translate/core';
import { Observable } from 'rxjs';
import { map } from 'rxjs/operators';
import { SimpleDialogComponent, SimpleDialogResult } from '../../../shared/dialog/simple-dialog.component';
import { getScript, isScriptLoading, isScriptRunning, scriptRun } from '../interactive-explorer.state';
import { RunResult, RunScript, Script } from '../scripts';
import { DeleteScriptAction, GetScriptAction, RunScriptAction, UpdateScriptAction } from '../scripts.actions';
import { IScriptsState } from '../scripts.state';
import { RunResultDialogComponent } from './result-dialog/result-dialog.component';

@Component({
  selector: 'oca-script-page-component',
  changeDetection: ChangeDetectionStrategy.OnPush,
  encapsulation: ViewEncapsulation.None,
  template: `
    <oca-ie-script [loading]="isLoading$ | async"
                   [isRunning]="isRunning$ | async"
                   [script]="script$ | async"
                   [runResult]="runResult$ | async"
                   (save)="onSave($event)" (run)="onRun($event)"
                   (showFullscreen)="onShowFullscreen($event)"
                   (remove)="onRemove($event)"></oca-ie-script>`,
})

export class ScriptPageComponent implements OnInit {
  isLoading$: Observable<boolean>;
  isRunning$: Observable<boolean>;
  script$: Observable<Script | null>;
  runResult$: Observable<RunResult | null>;


  constructor(private store: Store<IScriptsState>,
              private route: ActivatedRoute,
              private router: Router,
              private translate: TranslateService,
              private matDialog: MatDialog) {
  }

  ngOnInit() {
    this.store.dispatch(new GetScriptAction(parseInt(this.route.snapshot.params.scriptId, 10)));
    this.runResult$ = this.store.pipe(select(scriptRun));
    this.isRunning$ = this.store.pipe(select(isScriptRunning));
    this.isLoading$ = this.store.pipe(select(isScriptLoading));
    this.script$ = this.store.pipe(select(getScript), map(s => s ? { ...s } : s));
  }

  onSave(script: Script) {
    this.store.dispatch(new UpdateScriptAction(script));
  }

  onRun(runScript: RunScript) {
    this.store.dispatch(new RunScriptAction(runScript));
  }

  onRemove(script: Script) {
    if (script.source.length < 2000) {
      this.store.dispatch(new DeleteScriptAction(script.id));
    } else {
      this.matDialog.open(SimpleDialogComponent, {
        data: {
          ok: this.translate.instant('ie.yes'),
          cancel: this.translate.instant('ie.cancel'),
          message: this.translate.instant('ie.are_you_sure_remove_script', { name: script.name }),
          title: this.translate.instant('ie.confirmation'),
        },
      }).afterClosed().subscribe((result: SimpleDialogResult) => {
        if (result && result.submitted) {
          this.store.dispatch(new DeleteScriptAction(script.id));
        }
      });
    }
  }

  onShowFullscreen(runResult: RunResult) {
    this.matDialog.open(RunResultDialogComponent, { data: runResult });
  }

}
