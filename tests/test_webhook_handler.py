import base64
import concurrent.futures
import hashlib
import hmac
import json
import sqlite3
import sys
from pathlib import Path
from unittest.mock import patch
import pytest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from zoho_webhook_handler import Outbox, Receiver, ClaireDelivery, MAX_BODY

@pytest.fixture
def setup(tmp_path):
    box = Outbox(tmp_path / 'events.db')
    accounts = {'one': {'account_id': '101', 'zuid': '11', 'secret': 'a' * 32}, 'two': {'account_id': '202', 'zuid': '22', 'secret': 'b' * 32}}
    return box, Receiver(accounts, box)

def send(receiver, account='one', data=None, secret=None):
    raw = json.dumps(data or {'messageId': 9007199254740993, 'zuid': '11'}).encode()
    signature = base64.b64encode(hmac.new((secret or 'a'*32).encode(), raw, hashlib.sha256).digest()).decode()
    return receiver.accept('/zoho/' + account, raw, signature)

def rows(box):
    with box.connect() as db:
        return db.execute('SELECT account,message,state,receipt FROM events').fetchall()

def test_official_shape_and_large_id(setup):
    box,r=setup
    assert send(r)==200
    assert rows(box)[0][:2]==('101','9007199254740993')

@pytest.mark.parametrize('raw', [b'null', b'[]', b'1', b'"str"', b'{', b'\xff', b'{}', b'{"zuid":"11","messageId":true}'])
def test_malformed(setup,raw):
    box,r=setup
    sig=base64.b64encode(hmac.new(b'a'*32,raw,hashlib.sha256).digest()).decode()
    assert r.accept('/zoho/one',raw,sig)==400
    assert rows(box)==[]

def test_raw_body_signature_and_oversize(setup):
    box,r=setup
    assert r.accept('/zoho/one',b'{}','é')==401
    assert r.accept('/zoho/one',b'{}','sha256=abc')==401
    assert r.accept('/zoho/one',b'x'*(MAX_BODY+1),'')==413
    assert r.accept('/unknown',b'{}','')==404

def test_accounts_and_aliases(setup):
    box,r=setup
    assert send(r,'two',{'messageId':'1','zuid':'22'},'a'*32)==401
    assert send(r,'two',{'messageId':'1','zuid':'11'},'b'*32)==400
    assert send(r,'two',{'messageId':'1','zuid':'22'},'b'*32)==200
    assert send(r,data={'messageId':'1','zuid':'11','toAddress':'alias@example.invalid'})==200
    assert len(rows(box))==2

def test_folder_replay_and_restart(setup):
    box,r=setup
    for folder in ('inbox','archive'):
        assert send(r,data={'messageId':'1','zuid':'11','folderId':folder,'receivedTime':123})==200
    assert len(rows(Outbox(box.path)))==1

class Delivery:
    def __init__(self):self.calls=[]
    def send(self,*args):self.calls.append(args);return 'run-1'

def test_concurrent_claim(setup):
    box,r=setup;send(r);d=Delivery()
    with concurrent.futures.ThreadPoolExecutor(4) as pool:
        list(pool.map(lambda _:Outbox(box.path).dispatch(d),range(4)))
    assert len(d.calls)==1
    assert rows(box)[0][2:]==('admitted','run-1')

def test_uncertain_never_retried(setup):
    box,r=setup;send(r)
    class Failed:
        def send(self,*args):raise TimeoutError()
    assert box.dispatch(Failed())
    assert not box.dispatch(Delivery())
    assert rows(box)[0][2]=='uncertain'

def test_crash_claim_stays_held(setup):
    box,r=setup;send(r)
    with box.connect() as db:db.execute("UPDATE events SET state='sending'")
    assert not Outbox(box.path).dispatch(Delivery())

@pytest.mark.parametrize('url',['http://example.invalid/hooks/agent','https://example.invalid/other','https://user:pw@example.invalid/hooks/agent','https://example.invalid/hooks/agent?q=x'])
def test_token_destination_validation(url):
    with pytest.raises(ValueError):ClaireDelivery(url,'x'*32)

def test_actual_authenticated_hook_contract():
    class Response:
        status=200
        def __enter__(self):return self
        def __exit__(self,*args):pass
        def read(self,n):return b'{"ok":true,"runId":"receipt"}'
    class Opener:
        def open(self,request,timeout):
            data=json.loads(request.data)
            assert data['agentId']=='jlp-support'
            assert data['sessionMode']=='isolated' and data['deliver'] is False
            assert request.get_header('Authorization')=='Bearer '+'x'*32
            assert request.get_header('Idempotency-key')=='key'
            assert timeout==25
            assert 'subject' not in data
            return Response()
    d=ClaireDelivery('http://127.0.0.1:18789/hooks/agent','x'*32);d.opener=Opener()
    assert d.send('one','1','key')=='receipt'
