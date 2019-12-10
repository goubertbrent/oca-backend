export interface NewScript {
  name: string;
  source: string;
}

export interface LastScriptRun {
  date: string;
  user: string;
  request_id: string;
  task_id: string | null;
  url: string;
}

export interface ScriptFunction {
  name: string;
  last_run: LastScriptRun | null;
  line_number: number;
}

export interface Script {
  id: number;
  created_on: string;
  modified_on: string;
  author: string;
  name: string;
  source: string;
  functions: ScriptFunction[];
  version: number;
}

export interface CreateScriptPayload {
  name: string;
  source: string;
}

export interface RunScript {
  id: number;
  'function': string;
  deferred: boolean;
}

export interface RunResult extends LastScriptRun {
  result: string;
  succeeded: boolean;
  time: number;
  script: Script;
}
