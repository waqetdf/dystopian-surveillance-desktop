import copy
import json
import os
import random
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from backend.config import ConfigStore, default_config, validate, atomic_json
from backend.events import EventEngine, ambient_rgb, connection_phase
from backend.scenes import Library, local_file
from backend.service import Service
from backend.ai import AIClient, NoRedirect
from tools.deploy import install, uninstall, paths, BEGIN, verify_assets


class ConfigurationTests(unittest.TestCase):
    def test_default_layout_is_asymmetric_complete_and_valid(self):
        c=validate(default_config());self.assertAlmostEqual(sum(p['w']*p['h'] for p in c['panels']),1)
        self.assertGreater(len(set((p['w'],p['h']) for p in c['panels'])),3)
    def test_reject_overlap_offscreen_nan_and_injection(self):
        for mutate in [lambda c:c['panels'][0].update(x=.9),lambda c:c['panels'][1].update(x=0),
                       lambda c:c['panels'][0].update(w=float('nan')),lambda c:c['apps'][0].update(argv='echo unsafe'),
                       lambda c:c['ai'].update(url='http://example.com/api'),lambda c:c['panels'][0].update(id='../bad')]:
            with self.subTest(mutate=mutate):
                c=default_config();mutate(c)
                with self.assertRaises(ValueError):validate(c)
    def test_persistence_backup_and_private_permissions(self):
        with tempfile.TemporaryDirectory() as d:
            s=ConfigStore(Path(d));c=default_config();c['appearance']['gap']=9;s.save(c)
            self.assertEqual(ConfigStore(Path(d)).value['appearance']['gap'],9)
            self.assertEqual(s.path.stat().st_mode&0o777,0o600)
            c['appearance']['gap']=4;s.save(c)
            self.assertEqual(json.loads(s.path.with_suffix('.json.bak').read_text())['appearance']['gap'],9)
    def test_corrupt_config_is_preserved(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'config.json';p.write_text('{bad')
            s=ConfigStore(Path(d));self.assertTrue(s.warning);self.assertEqual(p.read_text(),'{bad')
    def test_profile_roundtrip(self):
        c=default_config();c['profiles']['Trabajo']=copy.deepcopy(c['panels']);validate(c)
        c['profiles']['Trabajo'][0]['x']=1
        with self.assertRaises(ValueError):validate(c)
    def test_no_credentials_in_defaults(self):
        self.assertNotIn('key',default_config()['ai']);self.assertFalse(default_config()['ai']['enabled'])


class EventTests(unittest.TestCase):
    def setUp(self):self.now=1000;self.engine=EventEngine({},random.Random(1),lambda:self.now)
    def test_cooldown_probability_and_memory(self):
        s={'id':'s','events':[{'id':'a','trigger':'open','probability':1,'cooldown':60,'lines':['hola']}]}
        self.engine.open('s');self.assertIsNotNone(self.engine.choose(s,'open'))
        self.now+=30;self.assertIsNone(self.engine.choose(s,'open'))
        self.now+=31;self.assertIsNotNone(self.engine.choose(s,'open'))
        self.engine.open('s');self.assertEqual(self.engine.memory['s']['visits'],2)
    def test_timer_hour_app_and_disabled(self):
        for trigger,extra,query in [('timer',{'after':20},'tick'),('hour',{'hour':3},'tick'),('app',{'app':'terminal'},'app'),('memory',{'minVisits':2},'open')]:
            e=EventEngine({},random.Random(1),lambda:self.now);e.open('s');e.open('s');self.now+=21
            s={'id':'s','events':[{'id':'e','trigger':trigger,'probability':1,'cooldown':0,'lines':['x'],**extra}]}
            self.assertIsNone(e.choose(s,query,frequency=0,app='terminal',hour=3))
            self.assertIsNotNone(e.choose(s,query,app='terminal',hour=3))
    def test_connection_state_is_visual_and_reconnectable(self):
        s=default_config()['connection'];self.assertEqual(connection_phase(100,s),0)
        self.assertAlmostEqual(connection_phase(122.5,s),.5);self.assertEqual(connection_phase(130,s),1)
        self.assertEqual(connection_phase(0,s),0);s['enabled']=False;self.assertEqual(connection_phase(500,s),0)
    def test_ambient_is_continuous_at_stops_and_midnight(self):
        for hour in (0,5,7,11,14,18,21,24):
            a=ambient_rgb(hour-.0001);b=ambient_rgb(hour+.0001)
            self.assertLessEqual(max(abs(x-y) for x,y in zip(a,b)),1)


class LibraryTests(unittest.TestCase):
    def test_builtins_have_unique_identity_real_animation_and_metadata(self):
        lib=Library(Path('/nonexistent'));self.assertEqual(len(lib.items),6)
        if os.environ.get('DSD_MEDIA_DIR'):self.assertEqual(len(lib.items),6);self.assertEqual(lib.warnings,[])
        for s in lib.items.values():
            self.assertTrue(s['personality']);self.assertTrue(s['events']);self.assertTrue(s['dialogues']['talk'])
            from urllib.parse import urlparse,unquote
            if not s['available']:continue
            video=Path(unquote(urlparse(s['videoUrl']).path))
            r=subprocess.run(['ffprobe','-v','error','-count_frames','-show_entries','stream=nb_read_frames,codec_name','-of','json',str(video)],capture_output=True,text=True,check=True)
            data=json.loads(r.stdout)['streams'][0];self.assertGreater(int(data['nb_read_frames']),48);self.assertEqual(data['codec_name'],'h264')
            # Decode and compare distant frames: a static image cannot pass.
            r=subprocess.run(['ffmpeg','-v','error','-i',str(video),'-vf','select=eq(n\\,0)+eq(n\\,48)','-vsync','0','-an','-f','framemd5','-'],capture_output=True,text=True,check=True)
            hashes=[l.split(',')[-1].strip() for l in r.stdout.splitlines() if not l.startswith('#')]
            self.assertEqual(len(hashes),2);self.assertNotEqual(hashes[0],hashes[1],s['id'])
    def test_optional_media_does_not_disable_scene_features(self):
        with patch.dict(os.environ,{'DSD_MEDIA_DIR':'/nonexistent/dsd-media'}):
            lib=Library(Path('/nonexistent'))
            self.assertEqual(len(lib.items),6);self.assertEqual(lib.warnings,[])
            self.assertEqual(sum(s['available'] for s in lib.items.values()),2)
            self.assertTrue(lib.items['station']['apps']);self.assertTrue(lib.items['station']['dialogues'])

    def test_pack_path_traversal_and_symlink_escape(self):
        with tempfile.TemporaryDirectory() as d:
            folder=Path(d)/'pack';folder.mkdir();outside=Path(d)/'private';outside.write_text('private')
            (folder/'link').symlink_to(outside)
            for name in ('../private','link',str(outside)):
                with self.assertRaises(ValueError):local_file(folder,name)
    def test_import_video_transcodes_and_preserves_original(self):
        with tempfile.TemporaryDirectory() as d:
            lib=Library(Path(d));source=ROOT/'assets/scenes/alley/scene.mp4';before=source.read_bytes()
            sid=lib.import_video(source,'Personal','Interiores',fps=12,quality=360)
            self.assertTrue((Path(d)/sid/'scene.mp4').exists());self.assertEqual(source.read_bytes(),before)
            self.assertEqual(lib.items[sid]['name'],'Personal')
    def test_import_pack_is_data_only(self):
        with tempfile.TemporaryDirectory() as d:
            source=Path(d)/'pack';source.mkdir();src=ROOT/'assets/scenes/alley'
            s=json.loads((src/'scene.json').read_text());s['id']='my-pack'
            (source/'scene.json').write_text(json.dumps(s))
            for f in ('scene.mp4','thumbnail.png'):(source/f).write_bytes((src/f).read_bytes())
            (source/'run.sh').write_text('should never execute')
            lib=Library(Path(d)/'library');lib.import_pack(source)
            self.assertFalse((Path(d)/'library/my-pack/run.sh').exists())
    def test_checksums(self):self.assertEqual(verify_assets(ROOT),11)


class ServiceTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name)
        self.env=patch.dict(os.environ,{'XDG_STATE_HOME':str(self.root/'state')});self.env.start()
        self.messages=[];self.s=Service(self.messages.append,ConfigStore(self.root/'cfg'),Library(self.root/'scenes'))
    def tearDown(self):self.s.pool.shutdown(wait=True,cancel_futures=True);self.env.stop();self.temp.cleanup()
    def test_no_network_without_explicit_optin(self):
        with patch('urllib.request.build_opener') as net:
            with self.assertRaises(ValueError):self.s.command({'op':'ai','scene':'alley','text':'hi'})
            self.s.command({'op':'open','scene':'alley'});self.s.command({'op':'talk','scene':'alley'});self.s.tick()
            net.assert_not_called()
    def test_single_active_scene_and_dialogue_sequence(self):
        self.s.command({'op':'open','scene':'alley'});self.s.command({'op':'open','scene':'apartment'})
        self.assertEqual(self.s.active,'apartment')
        self.s.command({'op':'talk','scene':'apartment'})
        self.assertEqual(len(self.messages[-1]['lines']),2)
        self.s.command({'op':'close'});self.assertIsNone(self.s.active)
    def test_launch_preserves_shell_metacharacters_as_literal_arguments(self):
        app=self.s.store.value['apps'][0];app['argv']=['python3','--literal','$(touch /tmp/no-dsd) ; |']
        with patch('subprocess.Popen') as popen:
            self.s.command({'op':'launch','scene':'alley','app':'terminal'})
            self.assertEqual(popen.call_args.args[0],app['argv'])
            self.assertFalse(popen.call_args.kwargs.get('shell',False))
    def test_launch_runs_real_program_and_keeps_metacharacters_literal(self):
        destination=self.root/'launched.json'; payload='$(touch NOT_EXECUTED); echo hello'
        app=self.s.store.value['apps'][0]
        app['argv']=[sys.executable,'-c','import pathlib,sys; pathlib.Path(sys.argv[1]).write_text(sys.argv[2])',str(destination),payload]
        self.s.command({'op':'launch','scene':'alley','app':'terminal'})
        self.s.children[-1].wait(timeout=5)
        self.assertEqual(destination.read_text(),payload)
    def test_unassociated_launch_rejected(self):
        with self.assertRaises(ValueError):self.s.command({'op':'launch','scene':'alley','app':'media'})
    def test_history_clear_and_visit_persistence(self):
        self.s.command({'op':'open','scene':'alley'});self.s.memory['alley']['history']=[{'role':'user','content':'private'}]
        self.s.command({'op':'clearHistory'})
        persisted=json.loads(self.s.memory_path.read_text());self.assertEqual(persisted['alley']['history'],[])
        self.assertEqual(persisted['alley']['visits'],1)
    def test_invalid_save_does_not_store_key_or_test_connection(self):
        cfg=default_config();cfg['appearance']['gap']=999
        with patch.object(self.s.ai.secrets,'put') as put:
            with self.assertRaises(ValueError):self.s.command({'op':'save','config':cfg,'next':{'op':'key','key':'secret'}})
            put.assert_not_called()


class PlaybackTests(unittest.TestCase):
    def test_fps_cache_is_real_reused_and_preserves_source(self):
        from backend.playback import prepare_copies
        source=ROOT/'assets/scenes/alley/scene.mp4';before=source.read_bytes()
        scene={'id':'alley','videoUrl':source.as_uri(),'frameRate':30}
        with tempfile.TemporaryDirectory() as d:
            cache=Path(d);urls=prepare_copies([scene],12,cache)
            from urllib.parse import unquote,urlparse
            result=Path(unquote(urlparse(urls['alley']).path))
            r=subprocess.run(['ffprobe','-v','error','-select_streams','v:0','-show_entries','stream=r_frame_rate','-of','json',str(result)],capture_output=True,text=True,check=True)
            self.assertEqual(json.loads(r.stdout)['streams'][0]['r_frame_rate'],'12/1')
            with patch('backend.playback.subprocess.run') as ffmpeg:
                self.assertEqual(prepare_copies([scene],12,cache),urls);ffmpeg.assert_not_called()
            self.assertEqual(prepare_copies([scene],60,cache),{})
        self.assertEqual(source.read_bytes(),before)


class InstallerTests(unittest.TestCase):
    def setUp(self):self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name);self.p=paths(self.root)
    def tearDown(self):self.temp.cleanup()
    def test_install_idempotent_update_uninstall_restores_and_preserves(self):
        hypr=self.p['config']/'hypr/hyprland.conf';hypr.parent.mkdir(parents=True);hypr.write_text('# personal\n$mainMod = SUPER\n')
        wrapper=self.p['bin']/'dsd';wrapper.parent.mkdir();wrapper.write_text('previous command')
        install(self.root,yes=True);first=(self.p['data']/'current').resolve()
        install(self.root,yes=True);self.assertEqual((self.p['data']/'current').resolve(),first)
        self.assertEqual(hypr.read_text().count(BEGIN),1)
        user=self.p['data']/'scenes/personal.mp4';user.parent.mkdir();user.write_bytes(b'user')
        cfg=self.p['config']/'dystopian-surveillance/config.json';atomic_json(cfg,{'my':'settings'})
        hypr.write_text(hypr.read_text()+'# added later\n')
        uninstall(self.root,yes=True)
        self.assertEqual(hypr.read_text(),'# personal\n$mainMod = SUPER\n# added later\n')
        self.assertEqual(wrapper.read_text(),'previous command');self.assertTrue(user.exists());self.assertTrue(cfg.exists())
        self.assertFalse((self.p['data']/'current').exists());uninstall(self.root,yes=True)
    def test_update_to_new_release_preserves_personal_config(self):
        import shutil
        install(self.root,yes=True);old=(self.p['data']/'current').resolve()
        user=self.p['config']/'dystopian-surveillance/config.json';atomic_json(user,{'personal':True})
        copyroot=self.root/'source'
        shutil.copytree(ROOT,copyroot,ignore=shutil.ignore_patterns('.git','work','__pycache__'))
        (copyroot/'VERSION').write_text('0.1.1-test\n')
        with patch('tools.deploy.SOURCE',copyroot):install(self.root,yes=True)
        self.assertNotEqual((self.p['data']/'current').resolve(),old)
        self.assertTrue(old.exists());self.assertEqual(json.loads(user.read_text()),{'personal':True})
        uninstall(self.root,yes=True);self.assertTrue(user.exists())
    def test_personal_modifications_to_managed_files_preserved(self):
        install(self.root,yes=True);wrapper=self.p['bin']/'dsd';wrapper.write_text('user modification')
        with self.assertRaises(ValueError):install(self.root,yes=True)
        uninstall(self.root,yes=True);self.assertEqual(wrapper.read_text(),'user modification')
    def test_symlink_targets_never_overwritten(self):
        target=self.root/'personal';target.write_text('safe');self.p['bin'].mkdir();(self.p['bin']/'dsd').symlink_to(target)
        with self.assertRaises(ValueError):install(self.root,yes=True)
        self.assertEqual(target.read_text(),'safe')
    def test_failed_deployment_rolls_back(self):
        hypr=self.p['config']/'hypr/hyprland.conf';hypr.parent.mkdir(parents=True);hypr.write_text('personal\n')
        real=Path.write_text
        def failing(path,*args,**kwargs):
            if path.name=='dystopian-surveillance.desktop':raise OSError('simulated disk failure')
            return real(path,*args,**kwargs)
        with patch.object(Path,'write_text',failing):
            with self.assertRaises(OSError):install(self.root,yes=True)
        self.assertEqual(hypr.read_text(),'personal\n');self.assertFalse((self.p['bin']/'dsd').exists())
        self.assertFalse((self.p['data']/'current').exists())


if __name__=='__main__':unittest.main()
