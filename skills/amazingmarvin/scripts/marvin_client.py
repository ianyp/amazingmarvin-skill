"""Validated Marvin operations. Network transport is injected explicitly."""
from datetime import date
import math


class MarvinError(Exception):
    def __init__(self, message, *, code='invalid_input', outcome_unknown=False, details=None):
        super().__init__(message)
        self.details = details
        self.code = code
        self.outcome_unknown = outcome_unknown


def valid_date(value):
    try:
        if not isinstance(value, str) or date.fromisoformat(value).isoformat() != value:
            raise ValueError
    except ValueError:
        raise MarvinError('Date must be a valid YYYY-MM-DD') from None
    return value


class Client:
    def __init__(self, token, *, transport, full_access=False):
        if not isinstance(full_access, bool):
            raise MarvinError("full_access must be boolean")
        self.full_access = full_access
        self._task_reminders_verified = False
        if not isinstance(token, str) or not token.strip() or any(ord(c) < 32 or ord(c) == 127 for c in token):
            raise MarvinError('Configure MARVIN_API_TOKEN', code='missing_credentials')
        self._token = token
        self._transport = transport

    def _call(self, method, path, body=None, *, literal=False, array=False, full=False, response=None, read_only=False):
        if full: self._require_full()
        write = method != "GET" and not read_only and path != "test"
        headers = {('X-Full-Access-Token' if self.full_access else 'X-API-Token'): self._token}
        if literal:
            headers['X-Auto-Complete'] = 'false'
        try:
            result = self._transport(method, path, headers, body)
        except MarvinError:
            raise
        except Exception:
            raise MarvinError('Request failed; verify remote state before repeating a write',
                              code='transport_error', outcome_unknown=write) from None
        if isinstance(result, dict) and result.get('error'):
            raise MarvinError('Marvin returned an API error', code='api_error')
        if array and (not isinstance(result, list) or any(not isinstance(item, dict) for item in result)):
            raise MarvinError('Unexpected API response', code='invalid_response')
        if response == 'object' and not isinstance(result, dict):
            raise MarvinError('Unexpected API object', code='invalid_response', outcome_unknown=write)
        if write and response is None and not (result == 'OK' or isinstance(result, dict) and isinstance(result.get('_id'), str) and result['_id']):
            raise MarvinError('Unrecognized write receipt; verify remote state', code='invalid_response', outcome_unknown=True)
        return result

    def today(self, day):
        return self._call('GET', 'todayItems?date=' + valid_date(day), array=True)

    def due(self, day):
        return self._call('GET', 'dueItems?by=' + valid_date(day), array=True)

    def add(self, fields):
        body = self._fields(fields, creating=True)
        if self.full_access: self._references(body)
        return self._call('POST', 'addTask', body, literal=True)

    def check_auth(self):
        result=self._call('POST', 'test')
        if result!='OK': raise MarvinError('Invalid authentication response',code='invalid_response')
        return result

    def categories(self):
        return self._call('GET', 'categories', array=True)

    def labels(self):
        return self._call('GET', 'labels', array=True)

    def children(self, parent_id):
        from urllib.parse import urlencode
        if not isinstance(parent_id, str) or not parent_id.strip():
            raise MarvinError('Parent ID required')
        return self._call('GET', 'children?' + urlencode({'parentId': parent_id}), array=True)

    def done(self, item_id, *, offset):
        if not isinstance(item_id, str) or not item_id.strip():
            raise MarvinError('Task ID required')
        if isinstance(offset, bool) or not isinstance(offset, int) or not -840 <= offset <= 840:
            raise MarvinError('Invalid timezone offset')
        return self._call('POST', 'markDone', {'itemId': item_id, 'timeZoneOffset': offset})

    @staticmethod
    def resolve_task(items, query):
        matches = [item for item in items if isinstance(item, dict) and
                   (item.get('_id') == query or item.get('title') == query)]
        if len(matches) != 1 or matches[0].get('db') != 'Tasks' or not matches[0].get('_id'):
            raise MarvinError('Choose one unambiguous task ID', code='ambiguous_target')
        return matches[0]['_id']

    def _require_full(self):
        if not self.full_access:
            raise MarvinError('This operation requires --full-access and a full-access token', code='missing_capability')

    @staticmethod
    def _id(value):
        if not isinstance(value, str) or not value.strip() or len(value) > 512 or any(ord(c)<32 for c in value):
            raise MarvinError('A nonempty ID is required')
        return value

    @staticmethod
    def _number(value, *, integer=False, minimum=0):
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value < minimum or value > 9007199254740991 or integer and value != int(value):
            raise MarvinError('Invalid numeric value')
        return value

    def _query(self, path, **params):
        from urllib.parse import urlencode
        return path + '?' + urlencode(params)

    def completed(self, day):
        return self._call('GET', self._query('doneItems', date=valid_date(day)), array=True)

    def blocks(self, day):
        return self._call('GET', self._query('todayTimeBlocks', date=valid_date(day)), array=True)

    def goals(self): return self._call('GET', 'goals', array=True)
    def kudos(self): return self._call('GET', 'kudos', response='object')
    def account(self):
        data = self._call('GET', 'me', response='object')
        return {key: data[key] for key in ('kudos', 'level', 'kudosRemaining', 'rewardPoints') if key in data and isinstance(data[key], (int, float)) and not isinstance(data[key], bool)}

    def tracked(self):
        data = self._call('GET', 'trackedItem')
        if data is not None and not isinstance(data, dict):
            raise MarvinError('Unexpected timer response', code='invalid_response')
        return data

    def tracks(self, task_ids=None, *, day=None, offset=0):
        if day is not None:
            if task_ids is not None: raise MarvinError('Choose date or task IDs')
            self._number(offset, integer=True, minimum=-840)
            if offset>840: raise MarvinError('Invalid timezone offset')
            body = {'date': valid_date(day), 'timeZone': -offset}
        else:
            if not isinstance(task_ids, list) or not 1 <= len(task_ids) <= 100:
                raise MarvinError('Provide 1–100 task IDs')
            body = {'taskIds': [self._id(i) for i in task_ids]}
        return self._call('POST', 'tracks', body, array=True, read_only=True)

    def habit(self, item_id):
        return self._call('GET', self._query('habit', id=self._id(item_id)), response='object')

    def habits(self, *, raw=False):
        return self._call('GET', 'habits?raw=1' if raw else 'habits', full=raw, array=True)

    def project(self, fields):
        body = self._fields(fields, project=True, creating=True)
        if self.full_access: self._references(body)
        body.setdefault('day', None)
        return self._call('POST', 'addProject', body, literal=True)

    def _fields(self, fields, *, project=False, creating=False):
        allowed = {'title', 'day', 'dueDate', 'estimateMinutes', 'parentId', 'labelIds', 'note', 'plannedWeek', 'plannedMonth', 'dailySection', 'bonusSection', 'customSection', 'timeBlockSection', 'backburner'}
        allowed.add('priority' if project else 'isStarred')
        if not isinstance(fields, dict) or not fields or set(fields)-allowed: raise MarvinError('Unsupported item fields')
        body = dict(fields)
        if creating or 'title' in body:
            if not isinstance(body.get('title'), str) or not body['title'].strip(): raise MarvinError('Title is required')
        for key in ('day','dueDate','plannedWeek'):
            if key in body:
                value=body[key]
                if value is None and key=='dueDate' or key=='day' and (value is None and project or value=='unassigned' and not project): continue
                valid_date(value)
                if key=='plannedWeek' and date.fromisoformat(value).weekday()!=0: raise MarvinError('plannedWeek must be a Monday')
        if 'plannedMonth' in body:
            value=body['plannedMonth']
            if not isinstance(value,str) or len(value)!=7: raise MarvinError('plannedMonth must be YYYY-MM')
            valid_date(value+'-01')
        for key in ('parentId','customSection','timeBlockSection'):
            if key in body: self._id(body[key])
        if 'note' in body and not isinstance(body['note'],str): raise MarvinError('Note must be text')
        if 'labelIds' in body:
            ids=body['labelIds']
            if not isinstance(ids,list) or len(ids)>100: raise MarvinError('Invalid labelIds')
            for i in ids: self._id(i)
            if len(set(ids))!=len(ids): raise MarvinError('Duplicate label IDs')
        if 'backburner' in body and not isinstance(body['backburner'],bool): raise MarvinError('backburner must be boolean')
        for key,values in [('priority',('high','mid','low')),('dailySection',('Morning','Afternoon','Evening')),('bonusSection',('Essential','Bonus'))]:
            if key in body and body[key] not in values: raise MarvinError('Invalid '+key)
        if 'isStarred' in body:
            self._number(body['isStarred'],integer=True,minimum=-1)
            if body['isStarred']>3: raise MarvinError('Invalid priority')
        if 'estimateMinutes' in body:
            minutes=self._number(body.pop('estimateMinutes'))
            if minutes>9007199254740991/60000: raise MarvinError('Estimate too large')
            body['timeEstimate']=round(minutes*60000)
        return body

    def document(self, item_id):
        data=self._call('GET', self._query('doc',id=self._id(item_id)),full=True,response='object')
        if data.get('_id') != item_id or data.get('deletedAt'):
            raise MarvinError('Document unavailable or mismatched',code='invalid_response')
        return data

    def _item(self,item_id, *, task_only=False):
        data=self.document(item_id)
        if data.get('db')!='Tasks' and (task_only or not (data.get('db')=='Categories' and data.get('type')=='project')):
            raise MarvinError('Expected a task' if task_only else 'Expected a task or project',code='wrong_type')
        return data

    def _references(self,body,item_id=None):
        if 'parentId' in body and body['parentId']!='unassigned':
            parent=body['parentId']; seen={item_id} if item_id else set()
            # Reject cycles and unbounded hierarchies; do not invent a parent.
            for _ in range(30):
                if parent in ('root','unassigned',None): break
                if parent in seen: raise MarvinError('Parent cycle')
                seen.add(parent); doc=self.document(parent)
                if doc.get('db')!='Categories': raise MarvinError('Parent must be a category/project')
                parent=doc.get('parentId')
            else: raise MarvinError('Parent hierarchy exceeds validation bound')
        if body.get('labelIds'):
            labels={x.get('_id'):x for x in self.labels()}
            if any(i not in labels for i in body['labelIds']): raise MarvinError('Unknown label ID')
            # Exclusivity is a profile setting, never inferred from label names.
            group_ids=[labels[i].get('groupId') for i in body['labelIds'] if labels[i].get('groupId')]
            if len(group_ids)==len(set(group_ids)): return
            groups=self.document('strategySettings.labelSettings.groups').get('val')
            if not isinstance(groups,dict): raise MarvinError('Cannot validate label groups',code='invalid_response')
            used=set()
            for i in body['labelIds']:
                group=labels[i].get('groupId')
                if group and groups.get(group,{}).get('isExclusive'):
                    if group in used: raise MarvinError('Mutually exclusive labels')
                    used.add(group)

    def _update(self,item_id,fields):
        import time
        now=int(time.time()*1000)
        setters=[]
        for key,val in fields.items():
            setters.extend([{'key':key,'val':val},{'key':'fieldUpdates.'+key,'val':now}])
        setters.append({'key':'updatedAt','val':now})
        return self._call('POST','doc/update',{'itemId':item_id,'setters':setters},full=True)

    def edit(self,item_id,fields,*,expected_rev=None):
        doc=self._item(item_id)
        if expected_rev is not None and doc.get('_rev')!=expected_rev:
            raise MarvinError('Document changed; reread before editing',code='conflict')
        body=self._fields(fields,project=doc.get('db')=='Categories')
        self._references(body,item_id)
        # This guards against observed changes, not an atomic server-side CAS.
        latest=self.document(item_id)
        if doc.get('_rev')!=latest.get('_rev'):
            raise MarvinError('Document changed during validation',code='conflict')
        return self._update(item_id,body)

    def add_subtasks(self,item_id,titles):
        import uuid
        if not isinstance(titles,list) or not 1<=len(titles)<=100 or any(not isinstance(t,str) or not t.strip() for t in titles):
            raise MarvinError('Provide 1–100 nonempty subtask titles')
        doc=self._item(item_id,task_only=True)
        existing=doc.get('subtasks') or {}
        if not isinstance(existing,dict): raise MarvinError('Unexpected subtask schema',code='invalid_response')
        ranks=[]
        for value in existing.values():
            if not isinstance(value,dict): raise MarvinError('Unexpected subtask schema',code='invalid_response')
            ranks.append(self._number(value.get('rank',0),minimum=-9007199254740991))
        rank=max([0]+ranks)
        fields={}; ids=[]
        for title in titles:
            sid=uuid.uuid4().hex; rank+=1; ids.append(sid)
            fields['subtasks.'+sid]={'_id':sid,'title':title,'done':False,'rank':rank}
        result=self._update(item_id,fields)
        return {'itemId':item_id,'subtaskIds':ids,'receipt':result}

    def record_habit(self,item_id,value=None,*,time_ms=None,undo=False):
        self._id(item_id)
        if not isinstance(undo,bool): raise MarvinError('undo must be boolean')
        body={'habitId':item_id,'updateDB':True}
        if undo:
            if value is not None or time_ms is not None: raise MarvinError('Undo takes no value or time')
            body['undo']=True
        else:
            body['value']=self._number(value,integer=True,minimum=-9007199254740991)
            body['time']=self._number(time_ms,integer=True)
        return self._call('POST','updateHabit',body,response='object')

    def event(self,fields):
        from datetime import datetime
        if not isinstance(fields,dict) or set(fields)-{'title','note','start','length'} or not {'title','start','length'}<=set(fields): raise MarvinError('Invalid event fields')
        if not isinstance(fields['title'],str) or not fields['title'].strip() or 'note' in fields and not isinstance(fields['note'],str): raise MarvinError('Invalid event text')
        self._number(fields['length'],integer=True,minimum=1)
        try:
            dt=datetime.fromisoformat(fields['start'])
            if dt.utcoffset() is None: raise ValueError()
        except (TypeError,ValueError): raise MarvinError('Event start requires ISO datetime with timezone') from None
        return self._call('POST','addEvent',fields,literal=True)

    def reward(self,action,day,*,item_id=None,points=None):
        endpoints={'claim':'claimRewardPoints','unclaim':'unclaimRewardPoints','spend':'spendRewardPoints'}
        if action not in endpoints: raise MarvinError('Unsupported reward action')
        body={'op':action.upper(),'date':valid_date(day)}
        if action in ('claim','unclaim'):
            body['itemId']=self._id(item_id)
            if action=='unclaim' and item_id=='MANUAL': raise MarvinError('Manual reward claims cannot be unclaimed')
        elif item_id is not None: raise MarvinError('Spend does not accept an item ID')
        if action in ('claim','spend'):
            self._number(points,minimum=0)
            if points==0: raise MarvinError('Points must be positive')
            body['points']=points
        elif points is not None: raise MarvinError('Unclaim does not accept points')
        data=self._call('POST',endpoints[action],body,response='object')
        return {key:data[key] for key in ('rewardPoints','kudos','level') if key in data and isinstance(data[key],(int,float))}

    def notebooks(self): return self._call('GET','notebooks',full=True,array=True)
    def notebook(self,*,item_id=None,parent_id=None):
        if (item_id is None)==(parent_id is None): raise MarvinError('Provide one notebook ID or parent ID')
        params={'id':self._id(item_id)} if item_id is not None else {'parentId':self._id(parent_id)}
        data=self._call('GET',self._query('notebook',**params),full=True,response='object')
        if 'notebook' not in data or not isinstance(data.get('pages'),list): raise MarvinError('Invalid notebook response',code='invalid_response')
        return data
    def page(self,item_id):
        doc=self.document(item_id)
        if doc.get('db')!='Pages': raise MarvinError('Expected a notebook page')
        return doc
    def reminders(self):
        data=self._call('GET','reminders',full=True)
        if data is None: return []
        if not isinstance(data,list) or any(not isinstance(r,dict) for r in data): raise MarvinError('Invalid reminder response',code='invalid_response')
        return data

    def _duration(self,times):
        if not isinstance(times,list) or len(times)%2: raise MarvinError('Incomplete tracking intervals',code='invalid_response')
        for value in times: self._number(value,integer=True)
        if times!=sorted(times): raise MarvinError('Invalid tracking interval order',code='invalid_response')
        return sum(times[i+1]-times[i] for i in range(0,len(times),2))

    def track(self,item_id,action):
        self._require_full()
        if action not in ('START','STOP'): raise MarvinError('Action must be START or STOP')
        self._item(item_id,task_only=True)
        result=self._call('POST','track',{'taskId':item_id,'action':action},response='object')
        stopped=result.get('stopId')
        if result.get('issues') is None: result['issues']=[]
        try:
            if not {'startId','stopId','stopTimes','issues'}<=set(result) or not isinstance(result['issues'],list):
                raise MarvinError('Invalid tracking response',code='invalid_response')
            if stopped:
                self._item(stopped,task_only=True)
                times=result['stopTimes']; duration=self._duration(times)
                self._update(stopped,{'times':times,'duration':duration})
        except MarvinError as error:
            raise MarvinError('Timer request succeeded; cache reconciliation required. Do not repeat the timer action.',code='partial_success',outcome_unknown=error.outcome_unknown,details={'timerActionApplied':True,'stoppedTaskId':stopped,'recovery':'reconcile-tracking for stoppedTaskId','cause':error.code}) from None
        return {'timer':result,'cacheUpdated':bool(stopped),'receiptOnly':True}

    def reconcile_tracking(self,item_id):
        self._item(item_id,task_only=True)
        rows=self.tracks([item_id]); matches=[r for r in rows if r.get('taskId')==item_id]
        if len(matches)!=1: raise MarvinError('Cannot uniquely reconcile tracked task',code='invalid_response')
        times=matches[0].get('times');duration=self._duration(times)
        return self._update(item_id,{'times':times,'duration':duration})

    def set_reminder(self,fields):
        # Manual reminders have no task metadata to synchronize. Task/due reminder
        # workflows stay gated until their client scheduling contract is verified.
        allowed={'reminderId','time','title','type','offset','snooze','autoSnooze','canTrack'}
        if not isinstance(fields,dict) or set(fields)-allowed: raise MarvinError('Invalid reminder fields')
        body=dict(fields)
        self._id(body.get('reminderId'))
        if body.get('type')!='M': raise MarvinError('Only standalone manual reminders are currently supported',code='unsupported_capability')
        timestamp=self._number(body.get('time'),integer=True,minimum=1)
        if timestamp>=100_000_000_000: raise MarvinError('Reminder time must be unix seconds, not milliseconds')
        if not isinstance(body.get('title'),str) or not body['title'].strip() or len(body['title'])>200: raise MarvinError('Reminder title must contain 1–200 characters')
        for key in ('offset','snooze'): self._number(body.setdefault(key,0),integer=True)
        for key in ('autoSnooze','canTrack'):
            if not isinstance(body.setdefault(key,False),bool): raise MarvinError('Invalid reminder boolean')
        return self._call('POST','reminder/set',{'reminders':[body]})

    def delete_reminder(self,reminder_id):
        self._id(reminder_id)
        matches=[r for r in self.reminders() if r.get('reminderId')==reminder_id]
        if len(matches)!=1 or matches[0].get('type')!='M':
            raise MarvinError('Choose one existing standalone manual reminder',code='ambiguous_target')
        return self._call('POST','reminder/delete',{'reminderIds':[reminder_id]})

    def download_attachment(self,item_id,uid,output):
        from marvin_download import download
        self._id(uid)
        doc=self._item(item_id)
        attachment=doc.get('attach_'+uid)
        if not isinstance(attachment,dict) or attachment.get('uid')!=uid or attachment.get('itemId')!=item_id:
            raise MarvinError('Attachment does not match item metadata')
        name=attachment.get('fileName')
        if not isinstance(name,str) or not name: raise MarvinError('Missing attachment filename')
        size=attachment.get('size')
        if isinstance(size,bool) or not isinstance(size,int) or not 0<=size<=20_000_000: raise MarvinError('Attachment exceeds 20 MB or has unknown size')
        url=self._call('POST','downloadAttachment',{'itemId':item_id,'uid':uid,'fileName':name},full=True,read_only=True)
        return download(url,output,size=size)

    def _reminder_metadata(self,doc,at,offset,snooze,auto_snooze):
        if at.utcoffset() is None: raise MarvinError('Reminder datetime requires timezone')
        if doc.get('day')!=at.date().isoformat(): raise MarvinError('Schedule the task on the reminder event day first')
        self._number(offset,integer=True);self._number(snooze,integer=True)
        if not isinstance(auto_snooze,bool): raise MarvinError('autoSnooze must be boolean')
        return {'taskTime':at.strftime('%H:%M'),'reminderOffset':offset,'reminderTime':str(int(at.timestamp())-offset*60),'snooze':snooze,'autoSnooze':auto_snooze}

    def _reminder_update(self,item_id,fields):
        try: return self._update(item_id,fields)
        except MarvinError as e:
            raise MarvinError('Server reminder changed; task metadata needs reconciliation. Do not replay server change.',code='partial_success',outcome_unknown=e.outcome_unknown,details={'itemId':item_id,'serverReminderChanged':True,'recovery':'reminder-reconcile','cause':e.code}) from None

    def set_task_reminder(self,item_id,at,*,offset=0,snooze=0,auto_snooze=False):
        if not self._task_reminders_verified:
            raise MarvinError('Task-linked reminders failed live server-list readback; this workflow is research-gated',code='unsupported_capability')
        from datetime import datetime
        try: instant=datetime.fromisoformat(at)
        except (TypeError,ValueError): raise MarvinError('Invalid reminder datetime') from None
        doc=self._item(item_id,task_only=True)
        fields=self._reminder_metadata(doc,instant,offset,snooze,auto_snooze)
        if int(instant.timestamp())<=0 or int(instant.timestamp())>=100_000_000_000: raise MarvinError('Invalid reminder time')
        row={'reminderId':item_id,'time':int(instant.timestamp()),'type':'T','title':doc.get('title','')[:200],'offset':offset,'snooze':snooze,'autoSnooze':auto_snooze,'canTrack':False}
        self._call('POST','reminder/set',{'reminders':[row]})
        result=self._reminder_update(item_id,fields)
        return {'itemId':item_id,'serverReceipt':True,'metadataReceipt':result,'notificationDelivered':'unverified'}

    def delete_task_reminder(self,item_id):
        if not self._task_reminders_verified:
            raise MarvinError("Task-linked reminder workflow is research-gated",code="unsupported_capability")
        self._item(item_id,task_only=True)
        matches=[r for r in self.reminders() if r.get('reminderId')==item_id]
        if len(matches)!=1 or matches[0].get('type')!='T': raise MarvinError('Choose one existing task-time reminder')
        self._call('POST','reminder/delete',{'reminderIds':[item_id]})
        return self._reminder_update(item_id,{'reminderTime':None,'reminderOffset':None,'snooze':None,'autoSnooze':None})

    def reconcile_task_reminder(self,item_id,*,deleted=False,timezone='Europe/London'):
        from datetime import datetime
        from zoneinfo import ZoneInfo
        doc=self._item(item_id,task_only=True)
        matches=[r for r in self.reminders() if r.get('reminderId')==item_id]
        if deleted:
            if matches: raise MarvinError('Server reminder still exists; cannot clear metadata')
            fields={'reminderTime':None,'reminderOffset':None,'snooze':None,'autoSnooze':None}
        else:
            if len(matches)!=1 or matches[0].get('type')!='T': raise MarvinError('No unique server task reminder to reconcile')
            row=matches[0];self._number(row.get('time'),integer=True,minimum=1)
            if row['time']>=100_000_000_000: raise MarvinError('Unexpected reminder time unit')
            at=datetime.fromtimestamp(row['time'],ZoneInfo(timezone))
            fields=self._reminder_metadata(doc,at,row.get('offset',0),row.get('snooze',0),row.get('autoSnooze',False))
        return self._update(item_id,fields)
