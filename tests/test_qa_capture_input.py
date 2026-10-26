import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
JAVA = Path(os.environ.get('VIRGOS_QA_JAVA_HOME', 'D:/proyectos/mc-server/.runtime/jdk-17.0.20.1+1')) / 'bin'

class CaptureInputTest(unittest.TestCase):
    def test_public_lease(self):
        scratch = Path(tempfile.mkdtemp(prefix='virgos-capture-test-'))
        print('Retained capture test:', scratch)
        sources = [ROOT / 'dev/dh-compat/qa/mc/virgos/qa/CaptureLease.java',
                   ROOT / 'dev/dh-compat/qa-tests/mc/virgos/qa/CaptureLeaseTest.java']
        compile = subprocess.run([str(JAVA / 'javac.exe'), '-J-Xmx256m', '-d', str(scratch), *map(str, sources)], capture_output=True, text=True)
        self.assertEqual(0, compile.returncode, compile.stdout + compile.stderr)
        run = subprocess.run([str(JAVA / 'java.exe'), '-Xmx256m', '-cp', str(scratch), 'mc.virgos.qa.CaptureLeaseTest'], capture_output=True, text=True)
        self.assertEqual(0, run.returncode, run.stdout + run.stderr)
        self.assertIn('CaptureLeaseTest PASS', run.stdout)

    def test_action_wiring(self):
        source = (ROOT / 'dev/dh-compat/qa/mc/virgos/qa/ClientProbe.java').read_text()
        self.assertIn('case "capture_attack"', source)
        self.assertIn('if (!captureLease.active()) client.mouseHandler.releaseMouse();', source)
        self.assertIn('KeyMapping.click(client.options.keyAttack.getKey());', source)
        self.assertIn('capture-input.json', source)
        self.assertIn('while(client.options.keyAttack.consumeClick())', source)
        # Pin real event routing: only subsequent END ticks may arm, never render.
        tick = source[source.index('    public void tick('):source.index('    @SubscribeEvent', source.index('    public void tick('))]
        self.assertLess(tick.index('if (event.phase != TickEvent.Phase.END) return;'), tick.index('updateCapture(true);'))
        self.assertLess(tick.index('updateCapture(true);'), tick.index('case "capture_attack"'))
        render = source[source.index('    public void rendered('):source.index('    @SubscribeEvent', source.index('    public void rendered('))]
        self.assertIn('updateCapture(false);', render)
        self.assertNotIn('updateCapture(true)', render)
        update = source[source.index('    private void updateCapture('):source.index('    /** Client input receipt')]
        self.assertIn('if(tick)captureLease.tick(captureScene(client),System.nanoTime());', update)
        self.assertIn('else captureLease.observe(captureScene(client),System.nanoTime());', update)
        self.assertIn('receipt.addProperty("armed",captureLease.armed());', source)
        self.assertIn('hit.getType()==net.minecraft.world.phys.HitResult.Type.BLOCK', source)
        self.assertIn('serverEventProven",false', source)


    def test_existing_actions(self):
        # Exercise the actual retained command bodies, not a rewritten behavior model.
        source = (ROOT / 'dev/dh-compat/qa/mc/virgos/qa/ClientProbe.java').read_text()
        cases = []
        for name in ('key', 'hold', 'look'):
            start = source.index('                case "' + name + '" ->')
            end = source.index('\n                case ', start + 1)
            cases.append(source[start:end])
        scratch = Path(tempfile.mkdtemp(prefix='virgos-capture-legacy-'))
        print('Retained legacy action test:', scratch)
        harness = r"""import java.util.*;
public class ExistingActions {
 static KeyMapping heldKey; static int heldTicks; static Client client=new Client(); static String queue="";
 static class KeyMapping {String name;boolean down;KeyMapping(String n){name=n;} String getName(){return name;}String getKey(){return name;}void setDown(boolean b){down=b;}static void click(String k){queue+=k+";";}}
 static class Player {float yaw,pitch;void setYRot(float f){yaw=f;}void setXRot(float f){pitch=f;}}
 static class Options {KeyMapping[] keyMappings={new KeyMapping("key.attack"),new KeyMapping("key.use")};}
 static class Client {Object screen;Player player=new Player();Options options=new Options();}
 static class Value {Object v; Value(Object v){this.v=v;}String getAsString(){return v.toString();}int getAsInt(){return ((Number)v).intValue();}float getAsFloat(){return ((Number)v).floatValue();}}
 static class Command {Map<String,Value> m=new HashMap<>();Command with(String k,Object v){m.put(k,new Value(v));return this;}Value get(String k){return m.get(k);}}
 static void apply(String action,Command command) {switch(action) {__CASES__ default -> throw new IllegalArgumentException();}}
 public static void main(String[] args){
 apply("key",new Command().with("name","key.attack"));
 apply("hold",new Command().with("name","key.use").with("ticks",12));
 apply("look",new Command().with("yaw",180f).with("pitch",20f));
 System.out.println(queue+"|"+heldKey.name+"|"+heldTicks+"|"+client.player.yaw+"|"+client.player.pitch);
 for(String invalid:List.of("key","hold")){try{apply(invalid,new Command().with("name","missing").with("ticks",12));}catch(Exception e){System.err.println(e.getClass().getSimpleName()+":"+e.getMessage());}}
 System.out.println(queue+"|"+heldKey+"|"+heldTicks+"|"+client.options.keyMappings[1].down);
 }
}""".replace('__CASES__', '\n'.join(cases))
        file = scratch / 'ExistingActions.java'
        file.write_text(harness, encoding='utf-8')
        compiled = subprocess.run([str(JAVA / 'javac.exe'), '-J-Xmx256m', '-d', str(scratch), str(file)], capture_output=True, text=True)
        self.assertEqual(0, compiled.returncode, compiled.stdout + compiled.stderr)
        run = subprocess.run([str(JAVA / 'java.exe'), '-Xmx256m', '-cp', str(scratch), 'ExistingActions'], capture_output=True, text=True)
        self.assertEqual(0, run.returncode)
        self.assertEqual('key.attack;|key.use|12|180.0|20.0\nkey.attack;|null|12|false\n', run.stdout)
        self.assertEqual('IllegalArgumentException:Unknown key missing\n' * 2, run.stderr)

if __name__ == '__main__':
    unittest.main()
