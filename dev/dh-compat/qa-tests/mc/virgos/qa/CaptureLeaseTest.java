package mc.virgos.qa;

/** Public lease/model tests, not Minecraft/Forge runtime proof. */
public final class CaptureLeaseTest {
    static final CaptureLease.Target TARGET = new CaptureLease.Target(48, 64, 48);
    static CaptureLease.Scene ready() { return scene(true,true,true,TARGET); }
    static CaptureLease.Scene scene(boolean focused,boolean inGame,boolean alive,CaptureLease.Target target) {
        return new CaptureLease.Scene("127.0.0.1:25575",focused,inGame,alive,target);
    }
    /** Models the mapped grab/startAttack/continueAttack ordering, not a replacement mining engine. */
    static class Input implements CaptureLease.Input {
        int grabs, clicks, downs, releases, ups, queuedClicks, guard, accepted, refused;
        boolean captured, down, failClick;
        public void grab() { grabs++; captured=true; guard=10000; }
        public boolean captured() { return captured; }
        public void click() { clicks++; queuedClicks++; if(failClick) throw new IllegalStateException("fixture"); }
        public void down(boolean value) {
            down=value;
            if(value) downs++;
            else { ups++; queuedClicks=0; }
        }
        public void release() { releases++; captured=false; }
        void naturalClientTick() {
            if(guard>0)guard--;
            while(queuedClicks>0) {
                queuedClicks--;
                if(guard>0)refused++;else accepted++;
            }
            if(!down)guard=0; // Actual idle continueAttack(false) clears; true does not.
        }
        String state() { return grabs+":"+clicks+":"+downs+":"+ups+":"+releases+":"+queuedClicks; }
    }
    static void check(boolean condition,String message) { if(!condition)throw new AssertionError(message); }
    static void rejected(Runnable action) {
        try { action.run();throw new AssertionError("accepted"); }
        catch(IllegalArgumentException | IllegalStateException expected) {}
    }
    static void released(Input input,CaptureLease lease) {
        check(!lease.active() && !input.down && !input.captured && input.queuedClicks==0,"Input leaked after cleanup");
    }
    static void arm(Input input,CaptureLease lease) {
        input.naturalClientTick();
        lease.tick(ready(),50_000_000L);
        check(lease.active() && lease.reason().equals("armed") && input.clicks==1 && input.down,"Not armed after idle client tick");
    }
    public static void main(String[] args) {
        Input oldOrdering=new Input(); oldOrdering.grab();oldOrdering.click();oldOrdering.down(true);oldOrdering.naturalClientTick();
        check(oldOrdering.refused==1 && oldOrdering.accepted==0 && oldOrdering.guard>0,"Mapped ordering model must reproduce early-click refusal");

        Input input=new Input();CaptureLease lease=new CaptureLease(input);
        lease.start("one",40,TARGET,ready(),0);
        check(input.clicks==0 && !input.down && input.queuedClicks==0,"Capture must remain idle before a full natural client tick");
        check(lease.reason().equals("warmup") && lease.remaining()==40,"Warmup must not spend requested hold ticks");
        for(int i=1;i<=20;i++)lease.observe(ready(),i*1_000_000L);
        check(input.clicks==0 && !input.down && input.guard==10000,"Render callbacks must never arm or reset vanilla guard");
        String warmup=input.state();
        rejected(()->lease.start("duplicate",40,TARGET,ready(),1));check(input.state().equals(warmup),"Duplicate mutated warmup");
        arm(input,lease);
        check(input.guard==0 && input.accepted==0,"Only idle client tick may reset model guard");
        for(int i=1;i<=39;i++) {
            input.naturalClientTick();lease.tick(ready(),(i+1)*50_000_000L);
            check(lease.active(),"Lease ended before all requested hold ticks");
        }
        check(input.accepted==1 && input.refused==0 && input.releases==0,"Initial armed click must reach model without release interruption");
        input.naturalClientTick();lease.tick(ready(),2_050_000_000L);released(input,lease);
        check(lease.reason().equals("completed"),"Completion reason");
        String finished=input.state();rejected(()->lease.start("one",40,TARGET,ready(),3));
        check(finished.equals(input.state()),"Replay mutated completed state");

        for(boolean armed : new boolean[]{false,true}) {
            for(CaptureLease.Scene bad : new CaptureLease.Scene[]{
                new CaptureLease.Scene(null,true,true,true,TARGET),
                new CaptureLease.Scene("external:25575",true,true,true,TARGET),
                scene(false,true,true,TARGET),scene(true,false,true,TARGET),scene(true,true,false,TARGET)}) {
                Input in=new Input();CaptureLease l=new CaptureLease(in);
                rejected(()->l.start("bad",40,TARGET,bad,0));check(in.state().equals("0:0:0:0:0:0"),"Rejected input mutated");
                l.start("good",40,TARGET,ready(),0);if(armed)arm(in,l);
                l.observe(bad,100_000_000L);released(in,l);
                if(!armed)check(in.clicks==0,"Interrupted warmup queued an attack");
            }
            Input timeoutInput=new Input();CaptureLease timeout=new CaptureLease(timeoutInput);
            timeout.start("timeout",100,TARGET,ready(),0);if(armed)arm(timeoutInput,timeout);
            timeout.observe(ready(),10_000_000_000L);released(timeoutInput,timeout);
            check(timeout.reason().equals("wall_timeout"),"Wall deadline includes warmup");
            Input cancelInput=new Input();CaptureLease cancel=new CaptureLease(cancelInput);
            cancel.start("cancel",40,TARGET,ready(),0);if(armed)arm(cancelInput,cancel);
            cancel.cancel("cancelled");String state=cancelInput.state();cancel.cancel("cancelled");
            released(cancelInput,cancel);check(state.equals(cancelInput.state()),"Repeated cleanup mutated input");
            Input lostInput=new Input();CaptureLease lost=new CaptureLease(lostInput);
            lost.start("lost",40,TARGET,ready(),0);if(armed)arm(lostInput,lost);
            lostInput.captured=false;lost.observe(ready(),100_000_000L);released(lostInput,lost);
        }
        for(CaptureLease.Target wrong : new CaptureLease.Target[]{null,new CaptureLease.Target(0,0,0)}) {
            Input in=new Input();CaptureLease l=new CaptureLease(in);l.start("wrong",40,TARGET,ready(),0);
            in.naturalClientTick();l.tick(scene(true,true,true,wrong),50_000_000L);released(in,l);
            check(in.clicks==0 && l.reason().equals("target_changed"),"Arming must revalidate actual BLOCK target");
        }
        for(int ticks : new int[]{0,101})rejected(()->new CaptureLease(new Input()).start("bad",ticks,TARGET,ready(),0));
        Input mismatch=new Input();rejected(()->new CaptureLease(mismatch).start("bad",40,new CaptureLease.Target(0,0,0),ready(),0));
        check(mismatch.grabs==0,"Initial target mismatch grabbed mouse");
        Input noCapture=new Input(){public void grab(){grabs++;}};CaptureLease failedGrab=new CaptureLease(noCapture);
        rejected(()->failedGrab.start("grab",40,TARGET,ready(),0));released(noCapture,failedGrab);check(noCapture.clicks==0,"Failed capture clicked");
        Input errorInput=new Input();errorInput.failClick=true;CaptureLease error=new CaptureLease(errorInput);
        error.start("error",40,TARGET,ready(),0);errorInput.naturalClientTick();
        rejected(()->error.tick(ready(),50_000_000L));released(errorInput,error);
        Input downFailure=new Input(){public void down(boolean value){super.down(value);if(!value)throw new IllegalStateException("cleanup");}};
        CaptureLease errorWarmup=new CaptureLease(downFailure);rejected(()->errorWarmup.start("error",40,TARGET,ready(),0));
        released(downFailure,errorWarmup);check(downFailure.releases==1,"Cleanup must release even after attack-up error");
        Input changing=new Input();CaptureLease changeAfterArm=new CaptureLease(changing);changeAfterArm.start("changing",1,TARGET,ready(),0);
        arm(changing,changeAfterArm);changeAfterArm.observe(scene(true,true,true,null),60_000_000L);
        check(changeAfterArm.active(),"Destroyed target after arming is not an interruption");
        changing.naturalClientTick();changeAfterArm.tick(ready(),100_000_000L);released(changing,changeAfterArm);
        System.out.println("CaptureLeaseTest PASS");
    }
}
