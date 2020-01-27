import { DatePipe } from '@angular/common';
import { ChangeDetectionStrategy, Component, OnInit } from '@angular/core';
import { select, Store } from '@ngrx/store';
import { Observable } from 'rxjs';
import { getScripts, isScriptLoading } from '../../interactive-explorer.state';
import { CreateScriptPayload, Script } from '../../scripts';
import { CreateScriptAction, GetScriptsAction } from '../../scripts.actions';
import { IScriptsState } from '../../scripts.state';

@Component({
  changeDetection: ChangeDetectionStrategy.OnPush,
  templateUrl: 'scripts-page.component.html',
  styles: [`
    .ie-fab-bottom-right {
      position: fixed;
      right: 16px;
      bottom: 16px;
    }`],
})
export class ScriptsPageComponent implements OnInit {
  scripts$: Observable<Script[]>;
  isCreatingScript$: Observable<boolean>;

  constructor(private store: Store<IScriptsState>,
              private datePipe: DatePipe) {
  }

  ngOnInit() {
    this.scripts$ = this.store.pipe(select(getScripts));
    this.store.dispatch(new GetScriptsAction());
    this.isCreatingScript$ = this.store.pipe(select(isScriptLoading));
  }

  createScript() {
    const payload: CreateScriptPayload = {
      name: 'Script ' + this.datePipe.transform(new Date(), 'dd/MM/y HH:mm'),
      source: `import json
import logging

from google.appengine.api import users
from google.appengine.ext import ndb


def run():
    return 'It works!'
`,
    };
    this.store.dispatch(new CreateScriptAction(payload));
  }
}
