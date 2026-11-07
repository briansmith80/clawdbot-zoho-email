"""Synthetic reviewer checks: no customer data or network mail delivery."""
import base64
import concurrent.futures
import hashlib
import hmac
import http.client
import json
import socket
import sys
import threading
from pathlib import Path
import pytest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from zoho_webhook_handler import Outbox, Receiver, ClaireDelivery, require_active, serve

def accounts():
    return {'route': {'account_id': '101', 'zuid': '11', 'secret': 'a'*32}}

def signed(raw):
    return base64.b64encode(hmac.new(b'a'*32, raw, hashlib.sha256).digest()).decode()

def test_route_rename_does_not_duplicate(tmp_path):
    box = Outbox(tmp_path/'events.db')
    raw = b'{"zuid":"11","messageId":"123","folderId":"inbox"}'
    assert Receiver(accounts(), box).accept('/zoho/route', raw, signed(raw)) == 200
    renamed = {'renamed': accounts()['route']}
    assert Receiver(renamed, box).accept('/zoho/renamed', raw, signed(raw)) == 200
    with box.connect() as db:
        assert db.execute('SELECT account,message FROM events').fetchall() == [('101', '123')]

@pytest.mark.parametrize('field,value', [('zuid','11'), ('account_id','101'), ('secret','a'*32)])
def test_duplicate_identity_or_secret_rejected(tmp_path,field,value):
    config = accounts()
    config['second'] = {'account_id':'202','zuid':'22','secret':'b'*32}
    config['second'][field] = value
    with pytest.raises(ValueError):
        Receiver(config,Outbox(tmp_path/'events.db'))

def active_config():
    return dict(deployment_role='active', active_host=socket.gethostname(),
                processing_owner='single-active', polling_mode='non-delivering',
                read_only_policy_verified=True)

@pytest.mark.parametrize('field,value', [('deployment_role','standby'),
    ('active_host','another-host.invalid'),('processing_owner','dual-active'),
    ('polling_mode','delivering'),('read_only_policy_verified',False)])
def test_activation_interlocks(field,value):
    config=active_config(); config[field]=value
    with pytest.raises(ValueError):require_active(config)

def test_standby_default_and_active():
    with pytest.raises(ValueError): require_active({})
    require_active(active_config())

@pytest.fixture
def http_receiver(tmp_path):
    box=Outbox(tmp_path/'events.db')
    server=serve(Receiver(accounts(),box),'127.0.0.1',0)
    thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    yield server,box
    server.shutdown();server.server_close();thread.join()

def request(server, raw, headers):
    conn=http.client.HTTPConnection(*server.server_address,timeout=3)
    conn.request('POST','/zoho/route',raw,headers)
    response=conn.getresponse();status=response.status;response.read();conn.close()
    return status

def test_http_valid_replay_wrong_signature_and_transfer_encoding(http_receiver):
    server,box=http_receiver
    raw=b'{"zuid":"11","messageId":123}'
    assert request(server,raw,{'X-Hook-Signature':signed(raw)})==200
    assert request(server,raw,{'X-Hook-Signature':signed(raw)})==200
    assert request(server,raw,{'X-Hook-Signature':'wrong'})==401
    assert request(server,raw,{'Transfer-Encoding':'chunked'})==400
    with box.connect() as db: assert db.execute('SELECT count(*) FROM events').fetchone()==(1,)

@pytest.mark.parametrize('length,expected',[('9'*4500,413),('invalid',400),('1048577',413)])
def test_http_bad_lengths(http_receiver,length,expected):
    server,_=http_receiver
    assert request(server,b'',{'Content-Length':length})==expected

def test_signed_deep_json_is_rejected(http_receiver):
    server,_=http_receiver
    raw=b'['*1200+b']'*1200
    assert request(server,raw,{'X-Hook-Signature':signed(raw)})==400

@pytest.mark.parametrize('body,status',[(b'{}',200),(b'[]',200),(b'{"ok":true}',200),
    (b'{"ok":true,"runId":""}',200),(b'x'*16385,200),
    (b'{"ok":true,"runId":"r"}',202),(b'not json',200)])
def test_bad_receipt_held(tmp_path,body,status):
    class Response:
        def __enter__(self):return self
        def __exit__(self,*args):pass
        def read(self,n):return body
    Response.status=status
    class Opener:
        def open(self,*args,**kwargs):return Response()
    delivery=ClaireDelivery('http://127.0.0.1:18789/hooks/agent','x'*32)
    delivery.opener=Opener()
    box=Outbox(tmp_path/'events.db');box.enqueue('101','123')
    assert box.dispatch(delivery)
    assert not box.dispatch(delivery)
    with box.connect() as db:assert db.execute('SELECT state FROM events').fetchone()==('uncertain',)

def test_crash_during_send_is_held(tmp_path):
    class Crashed:
        def send(self,*args):raise SystemExit()
    box=Outbox(tmp_path/'events.db');box.enqueue('101','123')
    with pytest.raises(SystemExit):box.dispatch(Crashed())
    class MustNotSend:
        def send(self,*args):pytest.fail('crash must not resend')
    assert not Outbox(box.path).dispatch(MustNotSend())

@pytest.mark.parametrize('path',[':memory:','events.db',''])
def test_nonpersistent_or_ambiguous_ledger_path_rejected(path):
    with pytest.raises(ValueError): Outbox(path)
